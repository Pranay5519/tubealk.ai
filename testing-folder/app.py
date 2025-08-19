import streamlit as st
from testing_models import chatbot , retrieve_all_threads , llm
from langchain_core.messages import HumanMessage
import uuid
#title
st.title("LangGraph Chatbot with Gemini")

#Functions
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

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
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk for message_chunk , metatdata in chatbot.stream(
                {'messages' : [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )   
        )
    st.session_state['message_history'].append({"role": "assistant", "content": ai_message})
    
