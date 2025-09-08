from yt_rag_model import * 
import uuid
import re
import os
import sqlite3
import shutil
from langchain_core.messages import HumanMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate

# ================== TEXT SPLITTING ==================
def text_splitter(transcript: str):
    """
    Splits transcript text into chunks for embeddings.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.create_documents([transcript])


# ================== EMBEDDINGS & RETRIEVER ==================
def generate_embeddings(chunks):
    """
    Generate FAISS embeddings from transcript chunks.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-MiniLM-L6-v2',
        model_kwargs={"device": "cpu"}  # ✅ Force CPU
    )
    return FAISS.from_documents(chunks, embeddings)


def retriever_docs(vector_store):
    """
    Convert FAISS vector store into a retriever.
    """
    return vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})


def format_docs(retrieved_docs):
    """
    Format retrieved docs into a single string.
    """
    return "\n\n".join(doc.page_content for doc in retrieved_docs)


def save_embeddings_faiss(thread_id: str, vector_store):
    """
    Save FAISS embeddings locally for a given thread.
    """
    save_dir = f"faiss_indexes/{thread_id}"
    os.makedirs("faiss_indexes", exist_ok=True)
    vector_store.save_local(save_dir)
    print(f"✅ Embeddings for {thread_id} saved at {save_dir}")


def load_embeddings_faiss(thread_id: str):
    """
    Load FAISS embeddings for a given thread.
    """
    load_dir = f"faiss_indexes/{thread_id}"
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

    if os.path.exists(load_dir):
        vector_store = FAISS.load_local(
            load_dir, embeddings, allow_dangerous_deserialization=True
        )
        retriever = retriever_docs(vector_store=vector_store)
        print(f"✅ Retriever for {thread_id} loaded from {load_dir}")
        return retriever
    else:
        raise FileNotFoundError(f"❌ No FAISS index found for thread_id={thread_id} at {load_dir}")

def clear_faiss_indexes(base_dir: str = "faiss_indexes"):
    """
    Deletes all files and subfolders inside faiss_indexes,
    but keeps the faiss_indexes folder itself.
    """
    if os.path.exists(base_dir):
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)       # delete file
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)   # delete folder
        print(f"✅ Cleared all contents inside: {base_dir}")
    else:
        print(f"⚠️ Base folder not found: {base_dir}")