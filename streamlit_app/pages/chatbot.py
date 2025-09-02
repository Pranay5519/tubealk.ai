import sys
import os
import streamlit as st
import uuid
from langchain_core.messages import HumanMessage

# Add the testing_folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../testing_folder")))
from utility_functions import *
from yt_shortVideo_model import retrieve_all_threads, build_chatbot, checkpointer

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(page_title="TubeTalk.ai - LectureChat", page_icon="💬", layout="wide")

#Hide Sidebar Home and other pages/files from displaying
hide_pages_style = """
<style>
[data-testid="stSidebarNav"] {display: none;}
</style>
"""
# =============================================================================
# STYLING
# =============================================================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .video-container {
        display: flex;
        justify-content: center;
        margin-bottom: 1.5rem;
    }
    iframe {
        border-radius: 12px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.2);
    }
    .chat-bubble-user {
        background: #667eea;
        color: white;
        padding: 0.8rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        max-width: 70%;
        align-self: flex-end;
    }
    .chat-bubble-assistant {
        background: #f1f1f1;
        padding: 0.8rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        max-width: 70%;
        align-self: flex-start;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1>💬 LectureChat</h1>
    <h3>Ask Questions, Get AI Answers with Timestamps</h3>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = []

if "chat_threads" not in st.session_state:
    st.session_state.chat_threads = retrieve_all_threads()

if "youtube_captions" not in st.session_state:
    st.session_state.youtube_captions = []

if "youtube_url" not in st.session_state:
    st.session_state.youtube_url = []

if "embed_url" not in st.session_state:
    st.session_state.embed_url = []

# =============================================================================
# SIDEBAR
# =============================================================================
st.sidebar.success("🚀 Start your interactive lecture chat")

st.sidebar.header("➕ Start New Chat")
input_url = st.sidebar.text_input("📺 YouTube Video URL")
thread_id = st.sidebar.text_input("📝 Conversation Name")

if st.sidebar.button("Start Chat"):
    if input_url and thread_id:
        reset_chat()
        youtube_captions = load_transcript(input_url)
        st.session_state.youtube_captions = youtube_captions
        st.session_state.youtube_url = input_url
        st.success("✅ Transcript loaded successfully!")
    else:
        st.warning("⚠️ Please enter both a YouTube URL and Conversation Name.")

st.sidebar.markdown("---")
st.sidebar.header("📂 My Conversations")
youtube_captions = st.session_state['youtube_captions']
chatbot = build_chatbot(youtube_captions)
sidebar_thread_selection(chatbot)

# =============================================================================
# MAIN CONTENT
# =============================================================================

# Show video if available
if st.session_state['youtube_url']:
    embed_url = get_embed_url(st.session_state['youtube_url'])
    st.markdown(f"""
    <div class="video-container">
        <iframe width="900" height="380"
        src="{embed_url}"
        frameborder="0" allow="accelerometer; autoplay; clipboard-write;
        encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
        </iframe>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("📺 Paste a YouTube URL in the sidebar to begin.")

# =============================================================================
# CHAT DISPLAY
# =============================================================================
st.subheader("💬 Chat with AI")

chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state["message_history"]:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            clean_text = msg['content'].split("Timestamp:")[0].strip()
            st.markdown(f"<div class='chat-bubble-assistant'>{clean_text}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# CHAT INPUT
# =============================================================================
user_input = st.chat_input("💡 Ask a question about this lecture...")
if user_input:
    if st.session_state['message_history'] == []:
        store_thread_id(thread_id=thread_id)
        save_transcript(thread_id=thread_id, captions=youtube_captions, youtube_url=input_url)

    # Add user message
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    st.markdown(f"<div class='chat-bubble-user'>{user_input}</div>", unsafe_allow_html=True)
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    chatbot = build_chatbot(st.session_state['youtube_captions'])

    with st.chat_message("assistant"):
        response = "".join(
            chunk.content for chunk, _ in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

        response_text, timestamp = map(str.strip, response.split("Timestamp:"))
        timestamp_url = f"{st.session_state['youtube_url']}&t={int(float(timestamp))}s"

        # Update embed with timestamp
        embed_url = get_embed_url(st.session_state['youtube_url'])
        timestamp_url_play = f"{embed_url}?start={int(float(timestamp))}&autoplay=1"
        st.session_state['embed_url'] = timestamp_url_play

        # Show assistant bubble
        st.markdown(f"<div class='chat-bubble-assistant'>{response_text}</div>", unsafe_allow_html=True)

        # Save assistant message
        st.session_state['message_history'].append({
            "role": "assistant",
            "content": response_text
        })

# =============================================================================
# WATCH BUTTON
# =============================================================================
if st.session_state['embed_url']:
    if st.button("▶️ Watch Answered Part"):
        st.markdown(f"""
        <div class="video-container">
            <iframe width="900" height="380"
            src="{st.session_state['embed_url']}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write;
            encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)
