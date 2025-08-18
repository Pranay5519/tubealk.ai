from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()  # load from .env file

# initialize google gemini model
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Define the state type that will be passed around the graph
class LLMState(TypedDict):
    question: str
    answer: str

# Node function
def qna(state: LLMState) -> LLMState:
    question = state["question"]
    prompt = f"answer the following question in one Word: {question}"
    answer = model.invoke(prompt).content
    state["answer"] = answer
    return state

# Build graph
graph = StateGraph(LLMState)
graph.add_node("qna", qna)
graph.add_edge(START, "qna")
graph.add_edge("qna", END)

# Compile workflow — this object can be imported
workflow = graph.compile()
