from dotenv import load_dotenv
load_dotenv()
from utility_functions import *
import sqlite3
import re
import uuid
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from youtube_transcript_api import YouTubeTranscriptApi

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

# ------------------ Build LLM (Gemini) ------------------
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# ------------------ System Message ------------------
system_message = SystemMessage(content="""
You are the YouTuber from the video, directly answering the viewer’s question.

Rules:
1. ONLY use the transcript provided below.
2. Give the answer in simple, clear sentences — without timestamps inside the text.
3. ALWAYS return the exact timestamp (in seconds) from the transcript line you used.
   - Do NOT round or estimate timestamps.
   - If multiple transcript parts are relevant, return the most direct one.
4. Do NOT add greetings, filler, or extra commentary.
5. If the transcript does not answer, say: "Sorry, I didn’t talk about that in this video."
""")

# ------------------ Structured Schema ------------------
class AnsandTime(BaseModel):
    answer: list[str] = Field(description="Answers to user's question (no timestamps here)")
    timestamps: float = Field(description="The time (in seconds) from where the answer was taken")

structured_model = model.with_structured_output(AnsandTime)

# ------------------ Chat State ------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ------------------ Chat Node ------------------
def chat_node(state: ChatState):
    # Build message list for model (system not stored in state)
    messages = [
        system_message,
        HumanMessage(content=f"Transcript:\n{youtube_captions}\n\nQuestion:\n{state['messages'][-1].content}")
    ]

    response = structured_model.invoke(messages)
    ai_text = f"{' '.join(response.answer)}\nTimestamp: {response.timestamps}"

    # Store only user + AI messages in memory
    return {
        "messages": [
            state["messages"][-1],
            AIMessage(content=ai_text)
        ]
    }

# ------------------ SQLite Checkpointer ------------------
conn = sqlite3.connect(database="delete.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)


# ------------------ Build Graph ------------------
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)


# StreamLit Code


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
        #save_to_txt_file(load_conversation(url))
        youtube_captions = load_transcript(url)
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
   
    with st.chat_message("assistant"):
        ai_message = st.write_stream(
            message_chunk for message_chunk , metatdata in chatbot.stream(
                {'messages' : [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )   
        )
            

    st.session_state['message_history'].append({"role": "assistant", "content": ai_message})
    

