#!/usr/bin/env python3
import re
import sys
import os
import argparse
from datetime import timedelta

def convert_time_format(srt_time):
    """Convert SRT time format (00:00:00,000) to ASS time format (0:00:00.00)"""
    hours, minutes, seconds_ms = srt_time.split(':')
    seconds, milliseconds = seconds_ms.split(',')
    
    # ASS format uses centiseconds (1/100 of a second)
    centiseconds = int(milliseconds) // 10
    
    # Format to ASS time format (removing leading zero from hours)
    ass_time = f"{int(hours)}:{minutes}:{seconds}.{centiseconds:02d}"
    return ass_time

def parse_srt(srt_file):
    """Parse SRT file and extract subtitle entries"""
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the content by double newline (which separates subtitle entries)
    subtitle_blocks = re.split(r'\n\n+', content.strip())
    subtitles = []
    
    for block in subtitle_blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # Extract subtitle number
        try:
            subtitle_number = int(lines[0])
        except ValueError:
            continue
        
        # Extract time codes
        time_line = lines[1]
        time_match = re.match(r'(\d+:\d+:\d+,\d+)\s+-->\s+(\d+:\d+:\d+,\d+)', time_line)
        if not time_match:
            continue
            
        start_time, end_time = time_match.groups()
        
        # Extract text (can be multiple lines) and join with a space
        text = ' '.join(lines[2:])
        
        # Convert times to ASS format
        start_time_ass = convert_time_format(start_time)
        end_time_ass = convert_time_format(end_time)
        
        subtitles.append({
            'number': subtitle_number,
            'start_time': start_time_ass,
            'end_time': end_time_ass,
            'text': text
        })
    
    return subtitles

def create_ass_dialogues(subtitles, style_name="Default"):
    """Create ASS dialogue lines from subtitles"""
    dialogues = []
    
    # Track previous text to remove duplicates
    prev_text = None
    counter = 0  # Initialize counter here
    
    for subtitle in subtitles:
        # Clean up text (remove HTML tags if present)
        text = re.sub(r'<[^>]+>', '', subtitle['text'])
        
        # Skip if this is a duplicate of the previous text
        if text == prev_text:
            continue
            
        prev_text = text
        counter += 1
        
        # Format as ASS dialogue line with sequential numbering
        dialogue = f"Dialogue: 1,{subtitle['start_time']},{subtitle['end_time']},{style_name},,0,0,0,,{text}"
        dialogues.append(dialogue)
    
    return dialogues

def write_ass_file(output_file, dialogues):
    """Write dialogue lines to an ASS file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for dialogue in dialogues:
            f.write(dialogue + '\n')

def main():
    parser = argparse.ArgumentParser(description='Convert SRT to ASS dialogue lines')
    parser.add_argument('input_file', help='Input SRT file path')
    parser.add_argument('-o', '--output', help='Output ASS file path')
    parser.add_argument('-s', '--style', default='Default', help='Style name for ASS dialogues (default: Default)')
    parser.add_argument('-d', '--deduplicate', action='store_true', help='Remove duplicate subtitle entries')
    
    args = parser.parse_args()
    
    # If output file not specified, use input filename with .ass extension
    if not args.output:
        base_name = os.path.splitext(args.input_file)[0]
        args.output = f"{base_name}.dialogue.ass"
    
    subtitles = parse_srt(args.input_file)
    dialogues = create_ass_dialogues(subtitles, args.style)
    write_ass_file(args.output, dialogues)
    
    print(f"Converted {len(dialogues)} subtitles from '{args.input_file}' to '{args.output}'")

if __name__ == "__main__":
    main() 