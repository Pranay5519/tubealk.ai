

import streamlit as st
from yt_shortVideo_model import *
from langchain_core.messages import HumanMessage
import uuid
from utility_functions import *
st.title("LangGraph Chatbot with Gemini")
#st.subheader(st.session_state['thread_id'])
# session states
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
    
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())  # Generate a new thread ID

if "chat_threads" not in st.session_state:
    st.session_state.chat_threads = retrieve_all_threads()
if "youtube_captions" not in st.session_state :
    st.session_state.youtube_captions = []

#Sidebar UI
st.sidebar.title("History")
if st.sidebar.button("new Chat"):
    reset_chat()
    
st.sidebar.header("My Conversations")
sidebar_thread_selection()

# Main UI
for message in st.session_state["message_history"]: # for loading chat history
    with st.chat_message(message["role"]):
        st.text(message["content"])


url = st.text_input("Enter YouTube Video URL: ")
if st.button("Load Transcripts.."):
    
    # Show a loading status box
    with st.status("Loading Transcripts...", expanded=True) as status:
        #st.video(url)
        save_to_txt_file(load_conversation(url))
        #youtube_captions = load_transcript(url)
        st.session_state.youtube_captions = youtube_captions
        

user_input = st.chat_input("Enter your question:")
if user_input:
    if st.session_state['message_history'] == []:
        save_thread_id_as_names(user_input)
        #check if thread_id history is empty or not
        
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)
    #st.session_state['thread_id'] - Stores Recent Thread_ID 
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}} # here thread_id  coming from function sidebar_thread_selection
    youtube_captions = st.session_state['youtube_captions']
    print("=== STREAMLIT DEBUG ===")
    print("youtube_captions type:", type(youtube_captions))
    print("youtube_captions length:", len(youtube_captions) if youtube_captions else 0)
    print("youtube_captions preview:", youtube_captions[:200] if youtube_captions else "EMPTY")

    with st.chat_message("assistant"):
        ai_message = chatbot.invoke(
        {"messages": [HumanMessage(content="what is this Video about?")]},
        config=CONFIG
    )['messages'][-1].content
            

    st.session_state['message_history'].append({"role": "assistant", "content": ai_message})
    
