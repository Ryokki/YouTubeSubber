import os
import re
import time
import requests
from typing import List, Dict, Union
from openai import OpenAI
import argparse


class LLMClient:
    """基础LLM客户端接口"""
    def chat_completion(self, messages, model, temperature):
        raise NotImplementedError("子类必须实现此方法")


class OpenAIClient(LLMClient):
    """OpenAI API客户端"""
    def __init__(self, api_key, base_url=None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def chat_completion(self, messages, model="gpt-3.5-turbo", temperature=0.3):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content


class DeepSeekClient(LLMClient):
    """DeepSeek API客户端"""
    def __init__(self, api_key, base_url="https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
        
    def chat_completion(self, messages, model="deepseek-chat", temperature=0.3):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"DeepSeek API调用失败: {response.text}")
            
        return response.json()["choices"][0]["message"]["content"]


class SrtTranslator:
    def __init__(self, client: LLMClient, model: str = "gpt-3.5-turbo"):
        self.client = client
        self.model = model
        self.batch_size = 30

    def parse_srt(self, file_path: str) -> List[Dict]:
        """Parse SRT file into a list of subtitle segments"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Split by double newline to get individual subtitle blocks
        subtitle_blocks = re.split(r'\n\n+', content.strip())
        subtitles = []

        for block in subtitle_blocks:
            lines = block.split('\n')
            if len(lines) < 3:
                continue

            try:
                index = int(lines[0].strip())
                timing = lines[1].strip()
                text = '\n'.join(lines[2:]).strip()

                subtitles.append({
                    'index': index,
                    'timing': timing,
                    'text': text
                })
            except Exception as e:
                print(f"Error parsing subtitle block: {block}")
                print(f"Error: {e}")

        return subtitles

    def translate_batch(self, batch: List[Dict], target_language: str) -> List[Dict]:
        """Translate a batch of subtitle segments"""
        # Prepare input for translation
        prompt = f"""You are an expert translator specializing in {target_language}, with deep understanding of cultural context and natural speech patterns. Your task is to translate the following video transcript segments.

Key translation principles to follow:
- Prioritize natural, conversational language over literal translations
- Maintain the original tone and style (casual, formal, humorous, etc.)
- Adapt idioms and expressions to culturally appropriate equivalents in {target_language}
- Ensure the translations sound fluid and native when spoken aloud
- Consider the context that this is spoken dialogue, not written text
- Preserve the emotional impact and intent of the original speech

Format requirements:
- Keep all [START_SEG#] and [END_SEG#] markers exactly as they appear
- Maintain exact segment numbering
- Place your translation between the START and END markers
- Do not add any additional text or explanations
- Keep one empty line between segments

Example format:
[START_SEG1]
¿Qué tal?
[END_SEG1]

[START_SEG2]
¿Cómo estás?
[END_SEG2]"""

        # Create input text with segment markers
        input_text = "\n\n".join([
            f"[START_SEG{i + 1}]\n{item['text']}\n[END_SEG{i + 1}]"
            for i, item in enumerate(batch)
        ])

        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": input_text}
            ]
            
            translation_text = self.client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.3
            )

            # Extract translated segments
            translated_segments = []
            pattern = r'\[START_SEG(\d+)\](.*?)\[END_SEG\1\]'
            matches = re.findall(pattern, translation_text, re.DOTALL)

            # Create a dictionary to store translations by segment number
            translations_dict = {int(num): text.strip() for num, text in matches}

            # Assign translations to the original batch
            for i, item in enumerate(batch):
                segment_num = i + 1
                if segment_num in translations_dict:
                    item['translated_text'] = translations_dict[segment_num]
                else:
                    item['translated_text'] = item['text']  # Fallback to original if translation missing

            return batch

        except Exception as e:
            print(f"Translation error: {e}")
            # In case of error, return untranslated batch
            for item in batch:
                item['translated_text'] = item['text']
            return batch

    def translate_srt(self, input_file: str, target_language: str, output_file: str):
        """Translate an entire SRT file"""
        subtitles = self.parse_srt(input_file)
        total_segments = len(subtitles)
        translated_subtitles = []

        print(f"Found {total_segments} subtitle segments to translate")

        # Process in batches
        for i in range(0, total_segments, self.batch_size):
            batch = subtitles[i:i + self.batch_size]
            print(
                f"Translating batch {i // self.batch_size + 1}/{(total_segments + self.batch_size - 1) // self.batch_size}...")

            translated_batch = self.translate_batch(batch, target_language)
            translated_subtitles.extend(translated_batch)

            # Sleep to avoid rate limiting
            if i + self.batch_size < total_segments:
                time.sleep(1)

        # Write translated subtitles to output file
        with open(output_file, 'w', encoding='utf-8') as file:
            for sub in translated_subtitles:
                file.write(f"{sub['index']}\n")
                file.write(f"{sub['timing']}\n")
                file.write(f"{sub['translated_text']}\n\n")

        print(f"Translation completed. Output saved to {output_file}")


def create_llm_client(api_type):
    """创建对应的LLM客户端"""
    if api_type.lower() == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL")
        return OpenAIClient(api_key=api_key, base_url=base_url), "gpt-3.5-turbo"
    
    elif api_type.lower() == "deepseek":
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        return DeepSeekClient(api_key=api_key, base_url=base_url), "deepseek-chat"
    
    else:
        raise ValueError(f"不支持的API类型: {api_type}, 请使用 'openai' 或 'deepseek'")


def main():
    parser = argparse.ArgumentParser(description='Translate SRT files')
    parser.add_argument('--input', type=str, required=True, help='Input SRT file path')
    parser.add_argument('--output', type=str, required=True, help='Output SRT file path')
    parser.add_argument('--api', type=str, default='openai', help='API provider: openai or deepseek')
    parser.add_argument('--language', type=str, default='Chinese', help='Target language for translation')
    parser.add_argument('--model', type=str, help='Override default model for the selected API')

    args = parser.parse_args()

    try:
        client, default_model = create_llm_client(args.api)
        model = args.model if args.model else default_model
        
        translator = SrtTranslator(client, model=model)
        translator.translate_srt(args.input, args.language, args.output)
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
