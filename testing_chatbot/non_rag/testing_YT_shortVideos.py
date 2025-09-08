from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated
import re
import os
from testing_chatbot.non_rag.utility_functions import *
os.environ["LANGCHAIN_PROJECT"] = "TubeTalkAI Testing"

# ------------------ Build LLM (Gemini) ------------------
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
checkpointer = InMemorySaver()
# Build graph
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

# Compile with checkpointing
chatbot = graph.compile(checkpointer=checkpointer)

# Config
CONFIG = {'configurable': {'thread_id': "newthread"}}
youtube_input = "https://www.youtube.com/watch?v=s3KnSb9b4Pk"
youtube_captions = load_transcript(youtube_input)
print("transcripts Loaded")
print("--"*100)
print("--"*100)

while True:
    user_input = input("User :")

    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat.")
        break
    if not checkpointer.storage:
        user_input = f"""
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
        {youtube_captions}

        Question:
        {user_input}

        Output format (for schema):
        - "answer": A list of 1–3 short strings that directly answer the question (no timestamps here).
        - "timestamps": The exact timestamp (in seconds) from the transcript where the answer was found.
        """
    result = chatbot.invoke(
                    {'messages' : [HumanMessage(content=user_input)]},
                    config=CONFIG
                )   
    last_msg = result["messages"][-1]  # get the last message
    if isinstance(last_msg, AIMessage):
        print("AI:", last_msg.content)

        