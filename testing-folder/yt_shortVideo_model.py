from dotenv import load_dotenv
load_dotenv()
import sqlite3
import uuid
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


# ------------------ Build LLM ------------------
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
6.Greet only if user does it
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
def chat_node(state: ChatState, youtube_captions):
    messages = [
        system_message,
        HumanMessage(content=f"Transcript:\n{youtube_captions}\n\nQuestion:\n{state['messages'][-1].content}")
    ]

    response = structured_model.invoke(messages)
    ai_text = f"{' '.join(response.answer)}\nTimestamp: {response.timestamps}"

    return {
        "messages": [
            state["messages"][-1],
            AIMessage(content=ai_text)
        ]
    }


# ------------------ SQLite Checkpointer ------------------
conn = sqlite3.connect(database="yt_ShortVideo.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# ------------------ Build Graph ------------------
graph = StateGraph(ChatState)

# instead of directly calling, wrap with youtube captions parameter
def build_chatbot(youtube_captions):
    # Create a new graph instance for each chatbot
    graph = StateGraph(ChatState)

    def _chat_node(state: ChatState):
        return chat_node(state, youtube_captions)

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

