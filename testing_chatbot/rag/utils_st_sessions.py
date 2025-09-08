import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import streamlit as st
from langchain_core.messages import  HumanMessage
from testing_chatbot.rag.yt_rag_model import build_chatbot 
from testing_chatbot.rag.utils_rag import load_embeddings_faiss 
from testing_chatbot.rag.utils_database import load_captions_from_db , load_url_from_db
def load_conversation(chatbot, thread_id):
    """
    Load conversation messages for a given thread from chatbot state.
    """
    return chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']


def add_thread(thread_id):
    """
    Add thread to session state if not already present.
    """
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def reset_chat():
    """
    Reset chat message history.
    """
    st.session_state['message_history'] = []


def add_threadId_to_chatThreads(thread_id):
    """
    Store new thread ID in session state.
    """
    recent_threads = st.session_state['chat_threads']
    if thread_id in recent_threads:
        st.warning("⚠️ Conversation name already exists")
    else:
        st.session_state['thread_id'] = thread_id
        add_thread(st.session_state['thread_id'])


def sidebar_thread_selection(chatbot):
    """
    Sidebar UI for selecting existing threads.
    """
    with st.spinner("Loading chats..." , show_time  = True):
        for thread_id in st.session_state['chat_threads'][::-1]:
            if st.sidebar.button(str(thread_id)):
                print("Sidebar Thread_Id CHECK - " , thread_id)
                st.session_state['thread_id'] = thread_id
                st.session_state['embed_url'] = []
                # Load conversation + captions + URL
                messages = load_conversation(chatbot, thread_id)
                st.session_state['youtube_captions'] = load_captions_from_db(thread_id)
                st.session_state['youtube_url'] = load_url_from_db(thread_id)
                print(f"Sidebar Selection -{thread_id} -> YouTube URL: {st.session_state['youtube_url']}")

                # Rebuild message history
                temp_history = []
                for msg in messages:
                    role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                    temp_history.append({"role": role, "content": msg.content})
                st.session_state['message_history'] = temp_history

                # Load retriever + chatbot
                try:
                    st.session_state['retriever'] = load_embeddings_faiss(thread_id)
                    st.session_state['chatbot'] = build_chatbot(st.session_state['retriever'])
                    st.success(f"Retriever loaded for {thread_id}")
                except FileNotFoundError as e:
                    st.error(str(e))
                st.subheader(thread_id)