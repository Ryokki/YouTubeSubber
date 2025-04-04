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

echo "Starting download and processing for: $YOUTUBE_URL"
echo "Target directory: $DIR_NAME"

# 1. Create video directory and enter it
mkdir -p "$DIR_NAME" && cd "$DIR_NAME"

# 2. Download YouTube video with subtitles and metadata
yt-dlp --format 'bv+ba' --write-auto-subs --sub-langs zh-Hans,en --write-link --write-thumbnail \
       --embed-metadata --merge-output-format mp4 --output 'video.mp4' "$YOUTUBE_URL" --sub-format "ttml" --convert-subs srt

# 3. Convert VTT subtitle files to SRT format or create empty ones if missing
# Chinese subtitles
echo "" >> video.zh-Hans.srt
# English subtitles
echo "" >> video.en.srt

# 4.0 Split Chinese srt
python ../split_srt.py video.zh-Hans.srt

# 4. Convert Chinese SRT to ASS format with dialogue style
python ../srt_to_ass_dialogue.py video.zh-Hans.srt -o video.zh-Hans.ass -s "Chinese" -d

# 5. Convert English SRT to ASS format with dialogue style
python ../srt_to_ass_dialogue.py video.en.srt -o video.en.ass -s "English" -d

# 6. Create final ASS subtitle file by combining template and language-specific ASS files
cp ../baoyu_template.ass ./video.ass && cat video.en.ass >> video.ass && cat video.zh-Hans.ass >> video.ass

# 7. Create new video!!!
ffmpeg -i './video.mp4' -vf ass='./video.ass' ./video_with_subtitle.mp4

echo "Video download and subtitle processing completed successfully in directory: $DIR_NAME" 

