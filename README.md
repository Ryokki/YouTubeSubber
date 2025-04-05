**YouTubeSubber - Generate video with embedding subtitle in english and chinese**

This is a toolkit for downloading YouTube videos and automatically embedding beautifully formatted bilingual subtitles (Chinese and English). 

The project helps create educational content or language learning materials by directly embedding dual-language subtitles into video files, making the content more accessible and easier to understand.



Thanks to

- https://baoyu.io/blog/translation/subtitle-and-ffmpeg
- https://github.com/ggml-org/whisper.cpp

# Run

```bash
./download_and_process_video.sh test https://www.youtube.com/watch\?v\=tSodBEAJz9Y\&pp\=ygUKbmV0d29ya2luZw%3D%3D
```

# TODO

- [x] Make it work (input url, generate subtitle ass and generate video with subtitle)
- [x] Use whisper to generate subtitle
- [x] Translate subtitle
- [x] Better subtitle split logic

