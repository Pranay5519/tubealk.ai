from testing_models import chatbot , retrieve_all_threads , llm
from langchain_core.messages import HumanMessage
import streamlit as st
def load_conversation(thread_id):
    return chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def reset_chat():
    st.session_state['message_history'] = []


def save_thread_id_as_names(user_input):
    prompt = f"you are a chatbot and Generate a title for the given conversation  in upto 2 words-> {user_input}"
    thread_id = llm.invoke(prompt).content
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    
    
    
def sidebar_thread_selection():
    for thread_id in st.session_state['chat_threads']:
        if st.sidebar.button(str(thread_id)):
            st.session_state['thread_id'] = thread_id
            messages = load_conversation(thread_id)
            temp_history = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    role = 'user'
                else:
                    role = 'assistant'
                temp_history.append({"role": role, "content": msg.content})
            st.session_state['message_history'] = temp_history