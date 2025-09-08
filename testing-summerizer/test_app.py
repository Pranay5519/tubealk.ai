import streamlit as st
import re
from model_langChain import *
from youtube_transcript_api import YouTubeTranscriptApi
st.title("TubeTalk.ai Summzerizer")

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
            
input_url = st.text_input("Enter youtube link here...")

if st.button("Summarize"):
    with st.status("🔍 Processing transcript...", expanded=True) as status:
        st.write("📥 Loading transcript...")
        youtube_captions = load_transcript(input_url)

        summarizer = YouTubeVideoSummarizer()

        st.write("✂️ Parsing transcript...")
        segments = summarizer.parse_transcript(youtube_captions)
        if not segments:
            st.error("No valid segments found in transcript.")
            status.update(label="❌ Failed", state="error")
        else:
            st.write("✅ Parsed transcript successfully")

            # Print first parsed segment (demo)
            print("Parsed Segments:")
            for segment in segments:
                print(f"[{segment.start_time}s] {segment.text}")
                break

            st.write("📝 Formatting transcript...")
            formatted = summarizer.format_transcript_for_llm(segments)

            st.write("🤖 Generating summary with AI...")
            summary = summarizer.summarize_video(youtube_captions)

            if "error" in summary:
                st.error(summary["error"])
                status.update(label="❌ Failed", state="error")
            else:
                st.write("📊 Formatting summary for display...")
                formatted_output = summarizer.format_summary_output(summary=summary)
                st.success("✅ Summary ready!")
                status.update(label="✅ Completed successfully", state="complete")

    st.write(formatted_output)
    st.download_button(
                    label="📥 Download Summary",
                    data=formatted_output,
                    file_name="video_summary.txt",
                    mime="text/plain"
                )
 