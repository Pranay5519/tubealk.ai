import streamlit as st
import re
from model import parser, extract_topics_from_transcript , parse_transcript , load_transcript
from utils_db import save_topics_to_db
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
    return url



# ✅ Cache transcript so it’s not fetched every rerun
@st.cache_data(show_spinner=False)
def get_transcript(url: str):
    captions = load_transcript(url)
    segments = parse_transcript(captions)
    return ["[" + str(s.start_time) + "s] " + s.text for s in segments]

# ✅ Cache LLM output so it’s not recomputed each button click
@st.cache_data(show_spinner=False)
def get_summary(formatted_text: str):
    return extract_topics_from_transcript(" ".join(formatted_text))

st.title("📹 TubeTalk.ai → Topics Extractor")

youtube_url = st.text_input("Enter YouTube URL:")
thread_id = st.text_input("Enter a unique Thread ID (for saving & retrieving):")
if youtube_url and thread_id:
    st.info("⏳ Fetching transcript...")
    formatted = get_transcript(youtube_url)  # cached now
    output = get_summary(formatted)  # cached now
    save_topics_to_db(thread_id,output.model_dump_json())  # Save to DB
    st.success("✅ Topics extracted & saved to DB!")
    embed_url = get_embed_url(youtube_url)
    st.subheader("📚 Extracted Topics")

    if "play_index" not in st.session_state:
        st.session_state.play_index = None

    for i, topic in enumerate(output.main_topics, 1):
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown(f"🎯 **Main Topic {i}: {topic.topic}**")
            #st.write(topic.content)
        with col2:
            if st.button("▶️ Play", key=f"play_main_{i}"):
                st.session_state.play_index = (f"main-{i}", topic.timestamp)

        with st.expander(f"🔽 Subtopics for: {topic.topic}"):
            for j, sub in enumerate(topic.subtopics, 1):
                sub_col1, sub_col2 = st.columns([4,1])
                with sub_col1:
                    st.markdown(f"   🔹 **Subtopic {i}.{j}:** {sub.subtopic}")
                    #st.write(sub.content)
                with sub_col2:
                    if st.button("▶️ Play", key=f"play_sub_{i}_{j}"):
                        st.session_state.play_index = (f"sub-{i}-{j}", sub.timestamp)

    if st.session_state.play_index:
        label, timestamp = st.session_state.play_index
        start_time = int(float(timestamp))
        video_url = f"{embed_url}?start={start_time}&autoplay=1"
        st.markdown(f"""
           
            <iframe width="800" height="450"
            src="{video_url}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
            encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
            </iframe>
        
        """, unsafe_allow_html=True)