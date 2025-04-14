import sys
from pathlib import Path

def merge_subtitles(template_path, en_path, zh_path, output_path):
    """
    合并中英文字幕，生成交替排列的格式
    
    :param template_path: 模板文件路径
    :param en_path: 英文字幕文件路径
    :param zh_path: 中文字幕文件路径
    :param output_path: 输出文件路径
    """
    try:
        # 读取模板文件
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 读取英文字幕
        with open(en_path, 'r', encoding='utf-8') as f:
            en_lines = f.readlines()
        
        # 读取中文字幕
        with open(zh_path, 'r', encoding='utf-8') as f:
            zh_lines = f.readlines()
        
        # 提取字幕正文部分（跳过[Script Info]和[V4+ Styles]等头部信息）
        en_dialogue = [line for line in en_lines if line.startswith('Dialogue:')]
        zh_dialogue = [line for line in zh_lines if line.startswith('Dialogue:')]
        
        if len(en_dialogue) != len(zh_dialogue):
            print("警告: 中英文字幕数量不匹配!")
        
        # 写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            # 先写入模板内容
            f.write(template)
            
            # 交替写入英文字幕和中文字幕
            for en, zh in zip(en_dialogue, zh_dialogue):
                f.write(en)
                f.write(zh)
            
        print(f"字幕合并完成，已保存到 {output_path}")
    
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("用法: python merge_subtitles.py <模板文件> <英文字幕> <中文字幕> <输出文件>")
        sys.exit(1)
    
    template_path = sys.argv[1]
    en_path = sys.argv[2]
    zh_path = sys.argv[3]
    output_path = sys.argv[4]
    
    merge_subtitles(template_path, en_path, zh_path, output_path)
