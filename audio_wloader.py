#!/usr/bin/env python3
"""
AudioWloader - Multi-platform Video Audio Extractor
Downloads videos from various platforms and extracts audio as WAV files.
Supports YouTube, Vimeo, and 1000+ other video sites via yt-dlp.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import yt_dlp


YDL_EXTRACTOR_ARGS = {
    # Avoid YouTube TV clients which can trigger DRM-protected formats.
    # Prefer the standard web/iOS clients.
    "youtube": {
        # Android client tends to expose at least one non-DRM format reliably.
        "player_client": ["android"],
    }
}


def is_video_url(url: str) -> bool:
    """Check if URL looks like a video URL."""
    # Basic URL validation
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        # yt-dlp supports many domains, so accept any HTTP/HTTPS URL
        # and let yt-dlp determine if it's supported
        return parsed.scheme in ('http', 'https')
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be filesystem-safe."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def parse_urls_from_text(file_path: Path) -> List[str]:
    """Parse URLs from a plain text file (one per line)."""
    urls = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                # Check if it looks like a URL
                if is_video_url(line):
                    urls.append(line)
    return urls


def parse_urls_from_json(file_path: Path) -> List[str]:
    """Parse URLs from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Support multiple JSON formats
    if isinstance(data, list):
        return [url for url in data if is_video_url(url)]
    elif isinstance(data, dict):
        # Try common keys
        for key in ['urls', 'URLs', 'videos', 'links']:
            if key in data and isinstance(data[key], list):
                return [url for url in data[key] if is_video_url(url)]
        # If no recognized key, try to find any list value
        for value in data.values():
            if isinstance(value, list):
                return [url for url in value if is_video_url(url)]
    
    raise ValueError(f"Could not parse URLs from JSON file: {file_path}")


def get_video_info(url: str, verbose: bool = False) -> Optional[dict]:
    """Extract video information without downloading."""
    ydl_opts = {
        'quiet': not verbose,
        'no_warnings': not verbose,
        'extractor_args': YDL_EXTRACTOR_ARGS,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'id': info.get('id', 'unknown'),
                'title': info.get('title', ''),
                'extractor': info.get('extractor', 'unknown'),
                'extractor_key': info.get('extractor_key', 'unknown'),
            }
    except Exception as e:
        if verbose:
            print(f"Error getting info for {url}: {e}", file=sys.stderr)
        return None


def download_audio(url: str, output_dir: Path, use_title: bool = False, verbose: bool = False) -> Optional[Path]:
    """
    Download video from any supported platform and extract audio as WAV.
    
    Returns the path to the downloaded WAV file, or None if failed.
    """
    # First, get video info to determine the ID and title
    info = get_video_info(url, verbose)
    if not info:
        print(f"Warning: Could not extract info from URL: {url}", file=sys.stderr)
        return None
    
    video_id = info['id']
    title = info.get('title', '')
    extractor = info.get('extractor', 'unknown')
    
    if verbose:
        print(f"  Platform: {extractor}")
        print(f"  Title: {title[:60]}..." if len(title) > 60 else f"  Title: {title}")
    
    # Configure yt-dlp options
    ydl_opts = {
        # Prefer any format that definitely has audio, then extract to WAV via ffmpeg.
        # (Some "bestaudio" formats can require tokens and may be unavailable.)
        'format': 'best[acodec!=none]/best',
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': not verbose,
        'no_warnings': not verbose,
        'extractor_args': YDL_EXTRACTOR_ARGS,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download
            ydl.download([url])
            
            # Determine output filename
            # First, check for the temporary file with video ID
            temp_file = output_dir / f"{video_id}.wav"
            
            if use_title and title:
                safe_title = sanitize_filename(title)
                final_filename = f"{safe_title}_({video_id}).wav"
                final_file = output_dir / final_filename
                
                if temp_file.exists():
                    temp_file.rename(final_file)
                    return final_file
            else:
                if temp_file.exists():
                    return temp_file
            
            # If the expected file doesn't exist, try to find any WAV file that was just created
            # (some extractors might use different naming)
            wav_files = list(output_dir.glob('*.wav'))
            if wav_files:
                # Get the most recently modified file
                latest = max(wav_files, key=lambda p: p.stat().st_mtime)
                return latest
            
            print(f"Warning: Downloaded file not found for {url}", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
        return None


def list_supported_sites() -> List[str]:
    """List some of the supported video sites."""
    # yt-dlp supports 1000+ sites, but we'll list some common ones
    common_sites = [
        'YouTube', 'Vimeo', 'Dailymotion', 'TikTok', 'Twitter/X',
        'Facebook', 'Instagram', 'Twitch', 'SoundCloud', 'Bandcamp',
        'TED', 'Coursera', 'Udemy', 'Khan Academy', 'BBC iPlayer',
        'and 1000+ more...'
    ]
    return common_sites


def main():
    parser = argparse.ArgumentParser(
        description='Download videos from various platforms and extract audio as WAV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Supported Platforms:
  AudioWloader supports 1000+ video sites including:
  YouTube, Vimeo, Dailymotion, TikTok, Twitter/X, Facebook, Instagram,
  Twitch, SoundCloud, Bandcamp, TED, Coursera, Udemy, and many more.

Examples:
  # From a text file
  python audio_wloader.py --input urls.txt --output ./audio_files

  # From JSON
  python audio_wloader.py --input urls.json --output ./audio_files

  # Direct URLs (mixed platforms)
  python audio_wloader.py --urls "https://youtu.be/VIDEO_ID" "https://vimeo.com/VIDEO_ID" --output ./audio_files
        '''
    )
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--input', '-i',
        type=Path,
        help='Input file (text or JSON) containing video URLs'
    )
    input_group.add_argument(
        '--urls', '-u',
        nargs='+',
        help='Video URLs as command-line arguments (supports multiple platforms)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('./audio_output'),
        help='Output directory for WAV files (default: ./audio_output)'
    )
    
    parser.add_argument(
        '--use-title',
        action='store_true',
        help='Include video title in filename'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output (shows platform detection and progress)'
    )
    
    parser.add_argument(
        '--list-sites',
        action='store_true',
        help='List some supported video sites and exit'
    )
    
    args = parser.parse_args()
    
    if args.list_sites:
        print("AudioWloader supports videos from these platforms (and 1000+ more):")
        for site in list_supported_sites():
            print(f"  - {site}")
        sys.exit(0)
    
    # Parse URLs
    urls = []
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)
        
        if input_path.suffix.lower() == '.json':
            urls = parse_urls_from_json(input_path)
        else:
            urls = parse_urls_from_text(input_path)
    else:
        urls = [url for url in args.urls if is_video_url(url)]
    
    if not urls:
        print("Error: No valid video URLs found in input", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.verbose:
        print(f"Found {len(urls)} URL(s)")
        print(f"Output directory: {output_dir}")
    
    # Download each URL
    successful = 0
    failed = 0
    
    for i, url in enumerate(urls, 1):
        if args.verbose:
            print(f"\n[{i}/{len(urls)}] Processing: {url}")
        else:
            print(f"[{i}/{len(urls)}] Processing: {url}")
        
        result = download_audio(url, output_dir, args.use_title, args.verbose)
        
        if result:
            successful += 1
            if args.verbose:
                print(f"✓ Saved: {result.name}")
            else:
                print(f"  ✓ Saved: {result.name}")
        else:
            failed += 1
            if args.verbose:
                print(f"✗ Failed: {url}")
            else:
                print(f"  ✗ Failed: {url}")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Download complete: {successful} successful, {failed} failed")
    print(f"Files saved to: {output_dir.absolute()}")
    print(f"{'='*50}")
    
    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
