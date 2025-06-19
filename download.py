from youtube_transcript_api import YouTubeTranscriptApi

from ipydex import IPS, activate_ips_on_exception
activate_ips_on_exception()

def download_german_subtitles(video_url):
    # Extract video ID from URL
    video_id = video_url.split('v=')[1].split('&')[0]

    api = YouTubeTranscriptApi()
    q, = api.list(video_id)
    q.fetch()

    try:
        # Try to fetch German (language code 'de') subtitles
        IPS()
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["de"])
        # Save to a file
        with open(f'{video_id}_german_subtitles.txt', 'w', encoding='utf-8') as f:
            for entry in transcript:
                f.write(f"{entry['text']}\n")
        print(f"German subtitles saved to {video_id}_german_subtitles.txt")
    except Exception as e:
        print(f"Could not download German subtitles: {e}")

# Example usage
video_url = "https://www.youtube.com/watch?v=niCVX4r79zs"
download_german_subtitles(video_url)
