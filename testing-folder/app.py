import streamlit as st
import uuid
from langchain_core.messages import HumanMessage
from utility_functions import *
from yt_shortVideo_model import retrieve_all_threads, build_chatbot, checkpointer

# =============================================================================
# SESSION STATE INITIALIZATION
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
# STYLING AND CSS
# =============================================================================

st.markdown(
    """
    <style>
    .fixed-video {
        position: fixed;
        top: 50px;
        left: 750px;
        transform: translateX(-50%);
        width: "100%";
        z-index: 10;
        background-color: white;
    }
    .block-container {
        padding-top: 50px; /* push chat below video */
    }
    .spacer {
            margin-top: 400px; /* same as video height to push content down */
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# =============================================================================
# SIDEBAR CONFIGURATION
# =============================================================================

st.sidebar.title("LangGraph Chatbot with Gemini")

st.sidebar.header("New Chat")
input_url = st.sidebar.text_input("Enter YouTube Video URL: ")
thread_id = st.sidebar.text_input("Give a Conversation Name : ")

# define Variables 
database_url = None
video_url = None
# =============================================================================
# MAIN CONTENT AREA - THREAD AND VIDEO DISPLAY
# =============================================================================

# Show thread id on Top (if exists)
print(">>> Checking Thread and Video display section")

# Show saved YouTube video (if exists)

if st.session_state['thread_id']:
    print("Loading video from session DataBase URL")
    database_url = st.session_state['youtube_url']
elif thread_id and input_url:
    print("Loading  video URL INPUT ")
    video_url = input_url
else:
    print("No video URL found")
    video_url = None
    st.warning('No URL provided')

if database_url:
    print("Displaying YouTube video from DataBase")
    embed_url = get_embed_url(database_url)
    st.markdown(f"""
        <div class="fixed-video">
            <iframe width="900" height="340"
            src="{embed_url}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
            encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
            </iframe>
        </div>
        """,
        unsafe_allow_html=True
    ) 


# =============================================================================
# SIDEBAR FUNCTIONALITY - NEW CHAT BUTTON
# =============================================================================

if st.sidebar.button("new Chat", key="new_chat_btn"):
    if input_url and thread_id:  # only load transcript if URL is provided
        reset_chat()  # clear old chat first
        database_url = None
        
        youtube_captions = load_transcript(input_url)
        st.session_state.youtube_captions = youtube_captions
        st.success("Transcripts Loaded Successfully..!")

        st.subheader(thread_id)
        print("Displaying YouTube video from Input")
        embed_url = get_embed_url(input_url)
        st.markdown(f"""
            <div class="fixed-video">
                <iframe width="900" height="340"
                src="{embed_url}"
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
                encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                </iframe>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif not input_url:
        st.warning("Please enter a YouTube URL before starting a new chat.")
    elif not thread_id:
         st.warning("Please enter a Conversation Name before starting a new chat.")

# =============================================================================
# SIDEBAR - CONVERSATION HISTORY
# =============================================================================
print("-" * 80)
st.sidebar.header("My Conversations")
youtube_captions = st.session_state['youtube_captions']
chatbot = build_chatbot(youtube_captions)
sidebar_thread_selection(chatbot)

# =============================================================================
# CHAT DISPLAY AND INTERACTION
# =============================================================================

# Display Chat History
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])

# Chat Input Processing
user_input = st.chat_input("Enter your question:")
if user_input:   
    if st.session_state['message_history'] == []:
        store_thread_id(thread_id=thread_id)
        save_transcript(thread_id=thread_id, captions=youtube_captions, youtube_url=input_url)
    
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    youtube_captions = st.session_state['youtube_captions']
    
    if st.session_state['youtube_url'] == []:
        extract_url = input_url
    else:
        extract_url = st.session_state['youtube_url']
        
    chatbot = build_chatbot(youtube_captions)

    with st.chat_message("assistant"):
        response = "".join(
            chunk.content for chunk, _ in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )
        
        response_text, timestamp = map(str.strip, response.split("Timestamp:"))
        timestamp_url = f"{extract_url}&t={int(float(timestamp))}s"
        #print("Extract url", extract_url)
        #print("video URL:", video_url)
        
        embed_url = get_embed_url(extract_url)
        timestamp_url_play = f"{embed_url}?start={int(float(timestamp))}&autoplay=1"
        
        #print("EMbede URL:", embed_url)
        #print("TIMESTAMP URL:", timestamp_url)
        #print("TIMESTAMP URL:", timestamp_url_play)
        #print("--" * 50)
        
        st.session_state['embed_url'] = timestamp_url_play
        st.write(response_text)
    
    st.session_state['message_history'].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": timestamp
        })

# =============================================================================
# WATCH BUTTON FUNCTIONALITY
# =============================================================================

if st.session_state['embed_url'] != []:    
    if st.button("▶️ Watch"):
        print("Watch button clicked - Displaying timestamped video")
        st.markdown(f"""
                    <div class="fixed-video">
                        <iframe width="900" height="340"
                        src="{st.session_state['embed_url']}"
                        frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
                        encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                        </iframe>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    print("=" * 80)