import re
import sys
import os
import argparse

def merge_short_segments(input_file, output_file, min_length=20):
    """
    合并SRT文件中过短的段落
    
    参数:
        input_file: 输入SRT文件路径
        output_file: 输出SRT文件路径
        min_length: 最小字符长度，小于此长度的段落将被合并 (默认20)
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 用正则表达式分割SRT文件的段落
    pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\d+\n|$)'
    segments = re.findall(pattern, content)
    
    if not segments:
        print("无法解析SRT文件或文件格式不正确")
        return
    
    merged_segments = []
    i = 0
    
    while i < len(segments):
        current_segment = list(segments[i])  # 转为列表以便修改
        
        # 如果当前不是最后一个段落，且下一个段落文本长度小于最小长度
        if i + 1 < len(segments) and len(segments[i+1][2].strip()) < min_length:
            # 更新当前段落的结束时间为下一个段落的结束时间
            time_parts = current_segment[1].split(' --> ')
            next_time_parts = segments[i+1][1].split(' --> ')
            current_segment[1] = f"{time_parts[0]} --> {next_time_parts[1]}"
            
            # 合并文本内容
            current_segment[2] = current_segment[2].strip() + " " + segments[i+1][2].strip()
            
            # 跳过下一个段落
            i += 2
        else:
            i += 1
        
        merged_segments.append(current_segment)
    
    # 重新编号并生成新的SRT内容
    output_content = ""
    for idx, segment in enumerate(merged_segments, 1):
        output_content += f"{idx}\n{segment[1]}\n{segment[2]}\n\n"
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)
    
    print(f"处理完成! 原始段落数: {len(segments)}, 合并后段落数: {len(merged_segments)}")

def main():
    parser = argparse.ArgumentParser(description='Translate SRT files')
    parser.add_argument('--input', type=str, required=True, help='Input SRT file path')
    parser.add_argument('--length', type=int, required=True, help='Length of segments to merge')
    args = parser.parse_args()
    
    merge_short_segments(args.input, args.input, args.length)

if __name__ == "__main__":
    main()
