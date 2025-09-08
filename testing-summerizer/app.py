import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi
from model_langChain import *  # your summarizer module

st.title("TubeTalk.ai Summarizer")

# ------------------- Helper Functions -------------------
def get_embed_url(url: str) -> str:
    """Convert any YouTube URL into an embeddable format."""
    match = re.search(r"v=([^&]+)", url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"
    match = re.search(r"youtu\.be/([^?&]+)", url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"
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
            captions = YouTubeTranscriptApi().fetch(video_id,languages=['en','hi']).snippets
            data = [f"{item.text} ({item.start})" for item in captions]
            return " ".join(data)
        except Exception as e:
            print(f"❌ Error fetching transcript: {e}")
            return None


# ------------------- Input -------------------
input_url = st.text_input("Enter YouTube link here...")

# Generate summary button
if st.button("Generate Summary"):
    st.session_state.generated = True
    st.session_state.play_index = None  # reset when generating
# ------------------- Summarize Button -------------------
if st.session_state.generated:
    st.info("📥 Loading transcript...")
    youtube_captions = load_transcript(input_url)

    if youtube_captions:
        summarizer = YouTubeVideoSummarizer()

        st.info("✂️ Parsing transcript...")
        segments = summarizer.parse_transcript(youtube_captions)
        st.success("✅ Parsed transcript successfully")

        # Optional: print first segment
        if segments:
            print(f"[{segments[0].start_time}s] {segments[0].text}")

        st.info("📝 Formatting transcript...")
        formatted = summarizer.format_transcript_for_llm(segments)

        st.info("🤖 Generating summary with AI...")
        response, parsed_output, summary = summarizer.summarize_video(youtube_captions)

        embed_url = "https://www.youtube.com/embed/3_TN1i3MTEU"

        # ------------------- Video Summary -------------------
        st.header("📹 VIDEO SUMMARY")
    st.markdown("---")
    st.subheader("Title")
    st.write(summary['title'])

    st.subheader("Duration")
    st.write(f"{summary.get('video_duration', 0)/60:.2f} mins")

    st.subheader("Total Segments")
    st.write(summary.get('total_segments', 0))

    st.subheader("📋 OVERVIEW")
    st.write(summary['overview'])

    st.subheader("🎯 KEY POINTS:")
    for i, point in enumerate(summary['key_points'], 1):
        st.markdown(f"**{i}. {point['content']}**")
        col1, col2 = st.columns([3,1])
        col1.write(f"Importance: {point['importance']}")

        if col2.button("⏰ Play", key=f"play_{i}"):
            st.session_state.play_index = i - 1  # store index

        # Placeholder for the video below the key point
        if st.session_state.play_index == i - 1:
            timestamp = int(float(point['timestamp']))
            timestamp_url = f"{embed_url}?start={timestamp}&autoplay=1"
            st.markdown(f"""
                <iframe width="800" height="450"
                src="{timestamp_url}"
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
                encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                </iframe>
            """, unsafe_allow_html=True)

    st.subheader("📚 MAIN TOPICS:")
    for topic in summary['main_topics']:
        st.write(f"• {topic}")

    st.subheader("⏱️ PACING ANALYSIS:")
    st.write(summary['duration_summary'])
            
    if st.button("Prepare and Download"):
        formatted_output = summarizer.format_summary_output(summary=summary)
        st.download_button(
                    label="📥 Download Summary",
                    data=formatted_output,
                    file_name="video_summary.txt",
                    mime="text/plain"
                )