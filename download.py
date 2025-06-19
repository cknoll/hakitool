import os
import json
import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi

from ipydex import IPS, activate_ips_on_exception
activate_ips_on_exception()

def slugify(text):
    """Convert text to a filename-safe slug"""
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces and multiple hyphens with single hyphen
    text = re.sub(r'[-\s]+', '-', text)
    # Remove leading/trailing hyphens and convert to lowercase
    return text.strip('-').lower()

def get_video_title(video_id):
    """Get video title from YouTube using oembed API"""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('title', video_id)
    except Exception as e:
        print(f"Could not fetch video title: {e}")
    return video_id

def download_german_subtitles(video_url):
    # Extract video ID from URL
    video_id = video_url.split('v=')[1].split('&')[0]

    # Create output directory if it doesn't exist
    os.makedirs('./output', exist_ok=True)

    # Get video title and create slugified filename
    video_title = get_video_title(video_id)
    slugified_title = slugify(video_title)

    api = YouTubeTranscriptApi()
    q, = api.list(video_id)
    q.fetch()

    try:
        # Try to fetch German (language code 'de') subtitles
        IPS()
        yt_ts_api = YouTubeTranscriptApi()
        transcript_obj = yt_ts_api.fetch(video_id, languages=["de"])

        # Save to JSON file with timestamps
        json_filename = f'./output/{slugified_title}_german_subtitles.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'video_id': video_id,
                'video_title': video_title,
                'video_url': video_url,
                'language': 'de',
                'transcript_snippets': transcript_obj.to_raw_data()
            }, f, ensure_ascii=False, indent=2)

        print(f"German subtitles saved to {json_filename}")
        print(f"Video title: {video_title}")

    except Exception as e:
        print(f"Could not download German subtitles: {e}")

# Example usage
# video_url = "https://www.youtube.com/watch?v=niCVX4r79zs"
video_url = "https://www.youtube.com/watch?v=U2vzHbyOhV4"
download_german_subtitles(video_url)
