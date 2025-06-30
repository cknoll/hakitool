import os
import json
import re
import requests
from datetime import datetime
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

def get_video_info(video_id):
    """Get video title and publish date from YouTube using oembed API"""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', video_id)

            # Try to get publish date from RSS feed as oembed doesn't provide it
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={video_id}"
            try:
                # Alternative: scrape the video page for publish date
                video_page_url = f"https://www.youtube.com/watch?v={video_id}"
                page_response = requests.get(video_page_url)
                if page_response.status_code == 200:
                    # Look for uploadDate in JSON-LD structured data
                    import re
                    json_ld_match = re.search(r'"uploadDate":"([^"]+)"', page_response.text)
                    if json_ld_match:
                        upload_date_str = json_ld_match.group(1)
                        # Parse ISO format date and extract just the date part
                        upload_date = datetime.fromisoformat(upload_date_str.replace('Z', '+00:00'))
                        publish_date = upload_date.strftime('%Y-%m-%d')
                        return title, publish_date
            except Exception:
                pass

            return title, None
    except Exception as e:
        print(f"Could not fetch video info: {e}")
    return video_id, None

def get_existing_video_urls_from_downloaded_json_files():
    """Get set of already downloaded video URLs from output JSON files."""
    existing_urls = set()
    output_dir = "./output"
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(output_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        existing_urls.add(data['video_url'])
                except (json.JSONDecodeError, KeyError):
                    continue
    return existing_urls

def get_playlist_videos(playlist_url):
    """Extract video IDs from a YouTube playlist URL."""
    try:
        video_ids = []
        # This is a placeholder - in practice you'd need to scrape the playlist page
        # or use the YouTube API to get the video IDs
        html = requests.get(playlist_url).text
        matches = re.findall(r'watch\?v=([a-zA-Z0-9_-]+)', html)
        if matches:
            video_ids = list(set(matches))
        return [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
    except Exception as e:
        print(f"Error getting playlist videos: {e}")
        return []

def download_german_subtitles(video_url, existing_urls=None):
    """Download German subtitles for a single video."""
    if existing_urls and video_url in existing_urls:
        print(f"Skipping already downloaded video: {video_url}")
        return "skipped"

    # Extract video ID from URL
    video_id = video_url.split('v=')[1].split('&')[0]

    # Create output directory if it doesn't exist
    os.makedirs('./output', exist_ok=True)
    os.makedirs('./output/fulltext', exist_ok=True)

    # Get video title and publish date, create slugified filename
    video_title, publish_date = get_video_info(video_id)
    slugified_title = slugify(video_title)

    # Prepend publish date to filename if available
    if publish_date:
        filename_prefix = f"{publish_date}_{slugified_title}"
    else:
        filename_prefix = slugified_title
        print("Warning: Could not fetch publish date, using title only")

    fulltext_lines  = []

    try:
        # Try to fetch German (language code 'de') subtitles
        # IPS()
        yt_ts_api = YouTubeTranscriptApi()
        transcript_obj = yt_ts_api.fetch(video_id, languages=["de"])

        # Save to JSON file with timestamps
        json_fpath = f'./output/{filename_prefix}_german_subtitles.json'
        fulltext_fpath = f'./output/fulltext/{filename_prefix}_german_subtitles.txt'
        result_dict = {
            "video_id": video_id,
            "video_title": video_title,
            "video_url": video_url,
            "publish_date": publish_date,
            "language": "de",
            "transcript_snippets": transcript_obj.to_raw_data(),
        }
        with open(json_fpath, 'w', encoding='utf-8') as fp:
            json.dump(result_dict, fp, ensure_ascii=False, indent=2)

        for snippet in result_dict["transcript_snippets"]:
            fulltext_lines.append(f"{snippet['text']}\n")

        with open(fulltext_fpath, 'w', encoding='utf-8') as fp:
            fp.writelines(fulltext_lines)

        print(f"German subtitles saved to {json_fpath}")
        print(f"Video title: {video_title}")

    except Exception as e:
        print(f"Could not download German subtitles: {e}")

# Example usage
# video_url = "https://www.youtube.com/watch?v=niCVX4r79zs"



def main():
    import time

    # Example playlist URL - replace with your desired playlist
    playlist_url = "https://www.youtube.com/playlist?list=PLMsZgEMEKvQKQDNhrHnxY9ScIcWMq5qzf"

    existing_urls = get_existing_video_urls_from_downloaded_json_files()

    if playlist_url:
        video_urls = get_playlist_videos(playlist_url)

        #IPS()
        for idx, url in enumerate(video_urls):
            try:
                print(f"{idx}:")
                res = download_german_subtitles(url, existing_urls)
                if res != "skipped":
                    time.sleep(10)  # Pause between downloads
            except:
                print("Problem with url", url)
    else:
        exit()
        # Fallback to single video download
        video_url = "https://www.youtube.com/watch?v=sNwK_3BVjKU"
        download_german_subtitles(video_url)

if __name__ == "__main__":
    main()
