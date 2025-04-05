#!/bin/bash

# Exit on error
set -e

# Check if required arguments are provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <directory_name> <youtube_url>"
    echo "Example: $0 my_video https://www.youtube.com/watch?v=U3aXWizDbQ4"
    exit 1
fi

# Get arguments
DIR_NAME="$1"
YOUTUBE_URL="$2"

# Store the script directory path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting download and processing for: $YOUTUBE_URL"
echo "Target directory: $DIR_NAME"
echo "Script directory: $SCRIPT_DIR"

# Create video directory and enter it
mkdir -p "$SCRIPT_DIR/output/$DIR_NAME"
cd "$SCRIPT_DIR/output/$DIR_NAME"

# Download YouTube video with subtitles and metadata
yt-dlp --format 'bv+ba' --write-auto-subs --sub-langs zh,en --write-link --write-thumbnail \
       --embed-metadata --merge-output-format mp4 --output 'video.mp4' "$YOUTUBE_URL"

# Generate English subtitle
ffmpeg -i video.mp4 -ar 16000 -ac 1 -c:a pcm_s16le video.wav
~/myproject/whisper.cpp/build/bin/whisper-cli -m ~/myproject/whisper.cpp/models/ggml-large-v2.bin -f video.wav -osrt true
mv video.wav.srt video.en.srt
python "$SCRIPT_DIR/merge_short_srt_segments.py" --input video.en.srt --length 20

# Translate English SRT to Chinese
 python "$SCRIPT_DIR/translate.py" --input video.en.srt --output video.zh.srt

# Split Chinese srt
python "$SCRIPT_DIR/split_srt.py" video.zh.srt

# Convert Chinese SRT to ASS format with dialogue style
python "$SCRIPT_DIR/srt_to_ass_dialogue.py" video.zh.srt -o video.zh.ass -s "Chinese" -d

# Convert English SRT to ASS format with dialogue style
python "$SCRIPT_DIR/srt_to_ass_dialogue.py" video.en.srt -o video.en.ass -s "English" -d

# Create final ASS subtitle file by combining template and language-specific ASS files
cp "$SCRIPT_DIR/baoyu_template.ass" ./video.ass && cat video.en.ass >> video.ass && cat video.zh.ass >> video.ass

# 7. Create new video 🎉
ffmpeg -i './video.mp4' -vf ass='./video.ass' ./video_with_subtitle.mp4

echo "Video download and subtitle processing completed successfully in directory: $DIR_NAME"
