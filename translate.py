import os
import re
import time
from typing import List, Dict
from openai import OpenAI
import argparse


class SrtTranslator:
    def __init__(self, client: OpenAI):
        self.client = client
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
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_text}
                ],
                temperature=0.3
            )

            translation_text = response.choices[0].message.content

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


def main():
    parser = argparse.ArgumentParser(description='Translate SRT files')
    parser.add_argument('--input', type=str, required=True, help='Input SRT file path')
    parser.add_argument('--output', type=str, required=True, help='Output SRT file path')

    args = parser.parse_args()

    target_language = 'Chinese'
    print(os.environ.get("OPENAI_API_KEY"), "xxxxx", os.environ.get("OPENAI_BASE_URL"))
    translator = SrtTranslator( OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url=os.environ.get("OPENAI_BASE_URL")))
    translator.translate_srt(args.input, target_language, args.output)


if __name__ == "__main__":
    main()
