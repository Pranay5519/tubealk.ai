import streamlit as st
import uuid
from langchain_core.messages import HumanMessage
from utility_functions import *
from yt_shortVideo_model import retrieve_all_threads, build_chatbot , checkpointer

#---MARKDOWN----

st.markdown(
    """
    <style>
        /* Sidebar width */
        [data-testid="stSidebar"] {
            min-width: 500px;   /* 👈 set your min width */
            max-width: 500px;   /* 👈 set your max width */
        }

        /* Sidebar content scroll if height is too big */
        [data-testid="stSidebar"] .css-1d391kg {
            overflow-y: auto;
            max-height: 90vh;  /* sidebar height relative to screen */
        }
    </style>
    """,
    unsafe_allow_html=True
)
# ------------------ Streamlit UI ------------------
st.title("LangGraph Chatbot with Gemini")

# Session States
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_threads" not in st.session_state:
    st.session_state.chat_threads = retrieve_all_threads()

if "youtube_captions" not in st.session_state:
    st.session_state.youtube_captions = []

# Sidebar UI
st.sidebar.title("New Chat")
url = st.sidebar.text_input("Enter YouTube Video URL: ")
thread_id =  st.sidebar.text_input("Give a Conversation Name : ")

if st.sidebar.button("new Chat", key="new_chat_btn"):
    reset_chat()  # clear old chat first
    if url and thread_id:  # only load transcript if URL is provided
       
        youtube_captions = load_transcript(url)
        st.session_state.youtube_captions = youtube_captions
        st.success("Transcripts Loaded Successfully..!")
    elif not url:
        st.warning("Please enter a YouTube URL before starting a new chat.")
        
    elif not thread_id :
         st.warning("Please enter a Conversation Name  before starting a new chat.")

# Chat History
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])



youtube_captions = st.session_state['youtube_captions']
chatbot = build_chatbot(youtube_captions)

st.sidebar.header("My Conversations")
sidebar_thread_selection(chatbot)

# Chat Input
user_input = st.chat_input("Enter your question:")
if user_input:   
    if st.session_state['message_history'] == []:
        store_thread_id(thread_id=thread_id)
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    youtube_captions = st.session_state['youtube_captions']

    chatbot = build_chatbot(youtube_captions)

    with st.chat_message("assistant"):
        ai_message = st.write_stream(
            message_chunk for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )
    

    st.session_state['message_history'].append({"role": "assistant", "content": ai_message})
