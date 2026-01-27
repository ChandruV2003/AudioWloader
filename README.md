# AudioWloader

A simple, standalone tool to download videos from **1000+ platforms** and extract audio as WAV files. Designed to work independently but can be integrated with transcription systems like MP2Text.

## Features

- **Multi-platform support**: Works with YouTube, Vimeo, Dailymotion, TikTok, Twitter/X, Facebook, Instagram, Twitch, SoundCloud, and 1000+ other video sites
- Extract audio as WAV files
- Support multiple input formats:
  - Plain text files with URLs (one per line)
  - JSON files with URL arrays
  - Command-line arguments
- Automatic platform detection
- Organized file storage on disk
- Progress tracking and error handling

## Supported Platforms

AudioWloader automatically detects and handles videos from:
- **Video Sites**: YouTube, Vimeo, Dailymotion, TikTok, Twitter/X, Facebook, Instagram, Twitch
- **Audio Sites**: SoundCloud, Bandcamp
- **Educational**: Coursera, Udemy, Khan Academy, TED
- **Streaming**: BBC iPlayer, and many more
- **And 1000+ other sites** supported by `yt-dlp`

Run `python audio_wloader.py --list-sites` to see more examples.

## Requirements

- Python 3.9+
- `yt-dlp` (multi-platform video downloader)
- `ffmpeg` (for audio conversion)

## Installation

```bash
# Clone or navigate to the project
cd AudioWloader

# Install Python dependencies
pip install -r requirements.txt

# Ensure ffmpeg is installed
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html
```

## Usage

### From a text file (one URL per line):
```bash
python audio_wloader.py --input urls.txt --output ./audio_files
```

### From a JSON file:
```bash
python audio_wloader.py --input urls.json --output ./audio_files
```

### From command-line arguments (mixed platforms):
```bash
python audio_wloader.py --urls "https://youtu.be/VIDEO_ID" "https://vimeo.com/VIDEO_ID" --output ./audio_files
```

### Example text file format:
```
# Comments start with #
https://youtu.be/VIDEO_ID_1
https://vimeo.com/VIDEO_ID_2
https://www.dailymotion.com/video/VIDEO_ID_3
```

### Example JSON format:
```json
{
  "urls": [
    "https://youtu.be/VIDEO_ID_1",
    "https://vimeo.com/VIDEO_ID_2",
    "https://www.dailymotion.com/video/VIDEO_ID_3"
  ]
}
```

## Output

Audio files are saved as WAV format with the naming convention:
- `{video_id}.wav` (default)
- Or `{video_title}_({video_id}).wav` if using `--use-title` flag

Files are organized in the specified output directory.

## Options

- `--input, -i`: Input file (text or JSON) containing video URLs
- `--urls, -u`: Direct URL arguments (space-separated, supports multiple platforms)
- `--output, -o`: Output directory (default: `./audio_output`)
- `--use-title`: Include video title in filename
- `--verbose, -v`: Verbose output (shows platform detection and progress)
- `--list-sites`: List some supported video sites and exit

## Examples

### Download from mixed platforms:
```bash
python audio_wloader.py --urls \
  "https://youtu.be/VIDEO_ID" \
  "https://vimeo.com/VIDEO_ID" \
  "https://www.tiktok.com/@user/video/VIDEO_ID" \
  --output ./audio_files --verbose
```

### Process a list of URLs with titles:
```bash
python audio_wloader.py --input urls.txt --output ./audio_files --use-title
```

## Integration with MP2Text

This tool is designed to work independently but can feed audio files to transcription systems:

```bash
# Download audio from various platforms
python audio_wloader.py --input urls.txt --output ./audio_files

# Then process with your transcription system
# (Your MP2Text transcriber can read the WAV files from ./audio_files)
```

## How It Works

AudioWloader uses `yt-dlp`, a powerful video downloader that supports 1000+ video sites. The tool:
1. Automatically detects the platform from the URL
2. Downloads the video (or audio stream if available)
3. Extracts audio using FFmpeg
4. Converts to WAV format
5. Saves with organized naming

No need to specify the platform - it's all automatic!

## License

MIT
