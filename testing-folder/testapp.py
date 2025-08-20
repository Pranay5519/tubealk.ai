# ------------------ Imports ------------------
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from youtube_transcript_api import YouTubeTranscriptApi
from typing import TypedDict, Annotated
import re
import os

os.environ["LANGCHAIN_PROJECT"] = "TubeTalkAI Testing"

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

# ------------------ Build LLM (Gemini) ------------------
google = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# ------------------ Build StateGraph Chatbot ------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    msgs = state["messages"]
    resp = google.invoke(msgs)
    return {"messages": [resp]}

# Checkpointer
checkpointer = InMemorySaver()

# Graph
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)
chatbot = graph.compile(checkpointer=checkpointer)

CONFIG = {'configurable': {'thread_id': "newthread"}}

# ------------------ Load YouTube Transcript ------------------
youtube_input = "https://www.youtube.com/watch?v=s3KnSb9b4Pk"
youtube_captions = load_transcript(youtube_input)
print("Transcript Loaded:", youtube_captions[:200], "...")

# Split & Embed transcript
chunks = text_splitter(youtube_captions)
vector_store = generate_embeddings(chunks)
retriever = retriever_docs(vector_store)

# ------------------ Chat Loop ------------------
output_dict = {"human": [], "ai": []}

while True:
    user_input = input("Enter your message: ")
    print("User:", user_input)

    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat.")
        break

    # get top-3 relevant context chunks
    retrieved_chunks = retriever.get_relevant_documents(user_input)
    context = format_docs(retrieved_chunks)

    # Build final prompt
    prompt = f"""
    You are a helpful assistant.
    Answer ONLY from the provided transcript context and also mention the time given in brackets.
    If the context is insufficient, just say you don't know.

    Context:
    {context}

    Question: {user_input}
    """

    result = chatbot.invoke(
        {'messages': [HumanMessage(content=prompt)]},
        config=CONFIG,
    )

    # Save & print response
    for msg in result['messages']:
        if isinstance(msg, HumanMessage):
            if msg.content not in output_dict['human']:
                output_dict['human'].append(msg.content)
        elif isinstance(msg, AIMessage):
            if msg.content not in output_dict['ai']:
                output_dict['ai'].append(msg.content)

    print("AI:", output_dict['ai'][-1])
