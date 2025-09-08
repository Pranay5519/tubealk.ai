from youtube_transcript_api import YouTubeTranscriptApi
from yt_rag_model import * 
import re



# ================== YOUTUBE UTILS ==================
def get_embed_url(url: str) -> str:
    """
    Convert any YouTube URL into an embeddable format.
    """
    # Match watch?v=VIDEO_ID
    match = re.search(r"v=([^&]+)", url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"
    
    # Match youtu.be/VIDEO_ID
    match = re.search(r"youtu\.be/([^?&]+)", url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"
    
    # Already embed link
    if "embed" in url:
        return url
    
    return url  # fallback


def load_transcript(url: str) -> str | None:
    """
    Fetch transcript for a YouTube video.
    """
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    if match:
        video_id = match.group(1)
        try:
            captions = YouTubeTranscriptApi().fetch(video_id).snippets
            data = [f"{item.text} ({item.start})" for item in captions]
            return " ".join(data)
        except Exception as e:
            print(f"❌ Error fetching transcript: {e}")
            return None
