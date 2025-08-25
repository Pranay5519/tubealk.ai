from test import *
import uuid
from langchain_core.messages import HumanMessage
import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi
import re
import sqlite3
from langchain.prompts import PromptTemplate


def load_conversation(thread_id):
    return chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def reset_chat():
    st.session_state['message_history'] = []


def save_thread_id_as_names(user_input):
    
    recent_ChatThreads = st.session_state['chat_threads']
    prompt = f""" You are a system that generates short, clear conversation titles.

        Rules:
        - Read the first user message of a chat.
        - Create a short descriptive title (max 5 words).
        - Be concise and topic-focused.
        - IMPORTANT: The title must NOT match any of the existing titles.

        Existing titles:
        {recent_ChatThreads}

        Example:
        Input: "I need help fixing a Python error in my code"
        Existing: ["Python Error Debugging", "FastAPI Setup Guide"]
        Output: "Python Code Fixing"

        Input: "Explain convolutional neural networks for my research paper"
        Existing: ["Machine Learning Basics", "CNN Research Explanation"]
        Output: "Convolutional Network Paper"

        Now generate a NEW title for this input:
        {user_input}"""
    thread_id = model.invoke(prompt).content
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
            
            
# _-----------------------------------------------------FUNCTIONS FOR RAG----------------------------------------------

# ------------------ Transcript Loader ------------------
def load_transcript(url: str) -> str | None:
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    if match:
        video_id = match.group(1)
        try:
            captions = YouTubeTranscriptApi().fetch(video_id).snippets
            # join text + start_time
            data = [f"{item.text} ({item.start})" for item in captions]
            return " ".join(data)
        except Exception as e:
            print(f"Error fetching transcript: {e}")
            return None

# ------------------ Text Splitter ------------------
def text_splitter(transcript):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.create_documents([transcript])

# ------------------ Vector Store & Retriever  ------------------
def generate_embeddings(chunks):
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    return FAISS.from_documents(chunks, embeddings)

def retriever_docs(vector_store):
    return vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

def format_docs(retrieved_docs):
    return "\n\n".join(doc.page_content for doc in retrieved_docs)



# CHecking Theads are empty or not
def is_thread_empty(conn, thread_id: str) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?;",
            (thread_id,)
        )
        count = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        return True  # Table not created yet
    return count == 0

# ------------------ Prompt Template ------------------
prompt_template = PromptTemplate(
    input_variables=["transcript", "question"],
    template="""
You are the YouTuber from the video, directly answering the viewer’s question.

Rules:
1. ONLY use the transcript provided below.
2. Give the answer in simple, clear sentences — without timestamps inside the text.
3. ALWAYS return the exact timestamp (in seconds) from the transcript line you used.
   - Do NOT round or estimate timestamps.
   - If multiple transcript parts are relevant, return the most direct one.
4. Do NOT add greetings, filler, or extra commentary.
5. If the transcript does not answer, say: "Sorry, I didn’t talk about that in this video."

Transcript:
{transcript}

Question:
{question}

Output format (for schema):
- "answer": A list of 1–3 short strings that directly answer the question (no timestamps here).
- "timestamps": The exact timestamp (in seconds) from the transcript where the answer was found.
"""
)


