import streamlit as st
from testing_models import chatbot , retrieve_all_threads , llm
from langchain_core.messages import HumanMessage
import uuid
from utility_functions import load_conversation, add_thread, reset_chat, save_thread_id_as_names, sidebar_thread_selection
#title
st.title("LangGraph Chatbot with Gemini")

# session states
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
    
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())  # Generate a new thread ID

if "chat_threads" not in st.session_state:
    st.session_state.chat_threads = retrieve_all_threads()

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
        
user_input = st.chat_input("Enter your question:")

if user_input:
    if st.session_state['message_history'] == []:
        save_thread_id_as_names(user_input)

    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)
    #print(st.session_state['thread_id'])
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}} # here thread_id  coming from function sidebar_thread_selection
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk for message_chunk , metatdata in chatbot.stream(
                {'messages' : [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )   
        )
    st.session_state['message_history'].append({"role": "assistant", "content": ai_message})
    
