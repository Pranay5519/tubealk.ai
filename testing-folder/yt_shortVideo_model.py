"""
LangGraph-based Chatbot using Gemini with SQLite checkpointing.
"""
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage ,AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
import re
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3
from pydantic import BaseModel , Field
# Load environment variables
load_dotenv()

# Initialize Gemini model
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# ChatState to store list of messages
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

#Structured Model BaseModel
class AnsandTime(BaseModel):
    answer: list[str] = Field(
        description="Answers to user's question (do NOT include timestamps here)"
    )
    timestamps: float = Field(
        description="The time (in seconds) from where the answer is taken"
    )
parser = PydanticOutputParser(pydantic_object=AnsandTime)
structured_model  = model.with_structured_output(AnsandTime)
# Node that takes history and gets next response
def chat_node(state: ChatState):
    user_message = state["messages"]
    response = structured_model.invoke(user_message)
    ai_text = f"{' '.join(response.answer)}\nTimestamp: {response.timestamps}"
    return {
        "messages": [
            state["messages"][-1],
            AIMessage(content=ai_text)
        ]
    }

# SQLite checkpoint database
conn = sqlite3.connect(database='delete.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# Build graph
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

# Compile with checkpointing
chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)

# utility functions for YouTube Chatbot
