
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage , HumanMessage , AIMessage
from youtube_transcript_api import YouTubeTranscriptApi
import re      
from langchain_google_genai import ChatGoogleGenerativeAI            
from dotenv import load_dotenv
load_dotenv()
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated
import re
import os
from langchain.prompts import PromptTemplate  
from utility_functions import *
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
# ------------------ Build LLM (Gemini) ------------------
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# ------------------ System Message ------------------
system_message = SystemMessage(content="""
You are the YouTuber from the video, directly answering the viewer’s question.

Rules:
1. ONLY use the transcript provided below.
2. Give the answer in clear, simple bullet points (not paragraphs).
3. Each bullet must include the exact timestamp (in seconds) from the transcript line used.
   - Do NOT round or estimate timestamps.
   - If multiple transcript parts are relevant, use separate bullets.
4. Do NOT add greetings, filler, or extra commentary.
5. If the transcript does not answer, say:
   - "Sorry, I didn’t talk about that in this video."
6. Greet only if the viewer greets first.
7. Always remember the viewer’s question when structuring the answer.
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
def chat_node(state: ChatState , retriever):
    user_question = state['messages'][-1].content
    
    # get context here
    retrieved_chunks = retriever.get_relevant_documents(user_question)
    def format_docs(retrieved_docs):
        return "\n\n".join(doc.page_content for doc in retrieved_docs)
    context = format_docs(retrieved_chunks)

    # build messages
    messages = [
        system_message,  # rules
        SystemMessage(content=f"Transcript:\n{context}"),  # context for model only
        HumanMessage(content=user_question)  # clean user input
    ]

    response = structured_model.invoke(messages)
    ai_text = f"{' '.join(response.answer)}\nTimestamp: {response.timestamps}"

    return {
        "messages": [
            state['messages'][-1],       # store user only
            AIMessage(content=ai_text)   # store ai only
        ]
    }
    
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
# ------------------  Checkpointer ------------------
conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# ------------------ Build Graph ------------------
def build_chatbot(retriever):
    # Create a new graph instance for each chatbot
    graph = StateGraph(ChatState)

    def _chat_node(state: ChatState):
        return chat_node(state, retriever)

    graph.add_node("chat_node", _chat_node)
    graph.add_edge(START, "chat_node")
    graph.add_edge("chat_node", END)
    chatbot = graph.compile(checkpointer=checkpointer)
    return chatbot

# ------------------ Retrieve All Threads ------------------
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)

