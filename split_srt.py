import re
import sys
import os


def split_long_line(text, max_length=35):
    # 检查文本是否已经包含\N分割
    if "\\N" in text:
        parts = text.split("\\N")
        # 检查所有分段是否都已经在长度限制内
        if all(len(part) <= max_length for part in parts):
            # 如果每段都已经够短，确保每段不以标点结尾
            cleaned_parts = [part.rstrip('，。、；：,.;:') for part in parts]
            return "\\N".join(cleaned_parts)
        # 如果有分段太长，可以考虑重新分割或保持原样
        # 这里选择保持原样，只清理标点符号
        cleaned_parts = [part.rstrip('，。、；：,.;:') for part in parts]
        return "\\N".join(cleaned_parts)
    
    # 如果文本未分割且足够短，直接返回
    if len(text) <= max_length:
        # 确保原始文本不以标点结尾
        text = text.rstrip('，。、；：,.;:')
        return text
    
    # 以下是原有的分割逻辑
    mid_point = len(text) // 2
    period_positions = [m.start() for m in re.finditer('[。.]', text)]
    
    if period_positions:
        best_period = min(period_positions, key=lambda x: abs(x - mid_point))
        if best_period > 0 and best_period < len(text) - 1:
            # 分割点前后可能有多个标点，需要去掉
            first_part = text[:best_period+1].rstrip('，。、；：,.;:')
            second_part = text[best_period+1:].lstrip('，。、；：,.;:')
            return first_part + "\\N" + second_part
    
    comma_positions = [m.start() for m in re.finditer('[，,]', text)]
    
    if comma_positions:
        best_comma = min(comma_positions, key=lambda x: abs(x - mid_point))
        if best_comma > 0 and best_comma < len(text) - 1:
            # 分割点前后可能有多个标点，需要去掉
            first_part = text[:best_comma+1].rstrip('，。、；：,.;:')
            second_part = text[best_comma+1:].lstrip('，。、；：,.;:')
            return first_part + "\\N" + second_part
    
    # 如果没有找到合适的分割点，就在中间分割
    # 确保分割后的两部分都不以标点结尾
    first_part = text[:mid_point].rstrip('，。、；：,.;:')
    second_part = text[mid_point:].lstrip('，。、；：,.;:')
    return first_part + "\\N" + second_part

def process_srt_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()  # 读取整个文件并去除首尾空白
    
    # 将内容按标准SRT格式拆分为字幕块
    # SRT格式中字幕块之间用两个换行符分隔
    subtitle_blocks = re.split(r'\n\s*\n', content)
    
    processed_blocks = []
    
    for block in subtitle_blocks:
        if not block.strip():  # 跳过空块
            continue
            
        lines = block.split('\n')
        if not lines:
            continue
            
        # 处理字幕块
        if lines[0].strip().isdigit():  # 第一行是序号
            subtitle_number = lines[0].strip()
            timestamp = lines[1] if len(lines) > 1 else ""
            
            # 连接剩余的文本行
            text_lines = lines[2:] if len(lines) > 2 else []
            full_text = ' '.join([line.strip() for line in text_lines])
            
            # 处理文本
            processed_text = split_long_line(full_text) if full_text else ""
            
            # 构建新的字幕块
            processed_block = f"{subtitle_number}\n{timestamp}\n{processed_text}"
            processed_blocks.append(processed_block)
        else:
            # 如果格式不正确，保持原样
            processed_blocks.append(block)
    
    # 使用一个空行连接所有处理过的字幕块
    processed_content = '\n\n'.join(processed_blocks)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(processed_content)

# 使用示例
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py input.srt [output.srt]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file
    process_srt_file(input_file, output_file)
    print(f"处理完成，结果已保存到 {output_file}")
