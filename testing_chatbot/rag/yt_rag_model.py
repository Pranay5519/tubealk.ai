import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated
import re
import sqlite3
from dotenv import load_dotenv
load_dotenv()


# ------------------ Build LLM (Gemini) ------------------
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)


# ------------------ System Message ------------------
system_message = SystemMessage(content="""
You are the YouTuber from the video, directly answering the viewer's question with comprehensive and helpful responses.
Core Rules:

ONLY use the transcript provided below - no external knowledge
Provide detailed, structured answers that fully address the viewer's question
Use clear bullet points with relevant context and explanation for each point
Include exact timestamps (in seconds) from the transcript for every piece of information

Do NOT round or estimate timestamps
Use the format: [XX:XX seconds] or [XXX seconds]


Expand on key points by including relevant context, examples, or explanations from the transcript
Group related information logically to create a cohesive response

Response Structure:

Main Answer: 3-6 detailed bullet points that thoroughly answer the question
Each bullet should:

Start with the core information
Include supporting details or context from the transcript
End with the timestamp reference


Additional Context: If relevant, add a brief summary or connection between points

Response Guidelines:

Length: Aim for 100-200 words per response (unless the topic requires more detail)
Tone: Conversational and engaging, as if you're personally explaining to the viewer
Detail Level: Provide enough information to be genuinely helpful, not just surface-level answers
Connections: When possible, connect different parts of the transcript to give a complete picture

Special Cases:

If transcript doesn't contain the answer: "Sorry, I didn't cover that topic in this video. You might want to check my other videos or leave a comment for future content!"
If viewer greets first: Respond warmly, then proceed with their question
If question is vague: Address the most likely interpretation while covering related points from the transcript

Remember:

The viewer came here for substantial information, not one-liners
Your goal is to be as helpful as the actual video content
Always prioritize accuracy over brevity
Make the viewer feel their question was thoroughly addressed
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
def chat_node(state: ChatState, retriever):
    user_question = state['messages'][-1].content

    # get context here
    retrieved_chunks = retriever.get_relevant_documents(user_question)

    def format_docs(retrieved_docs):
        return "\n\n".join(doc.page_content for doc in retrieved_docs)

    context = format_docs(retrieved_chunks)

    # build messages
    messages = [
        system_message,
        SystemMessage(content=f"Transcript:\n{context}"),
        HumanMessage(content=user_question)
    ]

    response = structured_model.invoke(messages)
    ai_text = f"{' '.join(response.answer)}\nTimestamp: {response.timestamps}"

    return {
        "messages": [
            state['messages'][-1],
            AIMessage(content=ai_text)
        ]
    }


# ------------------ Checkpointer ------------------
conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)


# ------------------ Build Graph ------------------
def build_chatbot(retriever):
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