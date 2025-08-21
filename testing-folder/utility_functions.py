from testing_models import chatbot , retrieve_all_threads , llm
from langchain_core.messages import HumanMessage
import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi
import re

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
