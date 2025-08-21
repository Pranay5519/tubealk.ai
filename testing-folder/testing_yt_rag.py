# ------------------ Imports ------------------
from dotenv import load_dotenv
load_dotenv()
from utility_functions import *
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
#os.environ["LANGCHAIN_PROJECT"] = "TubeTalkAI Testing"

# ------------------ Build LLM (Gemini) ------------------
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

#--------------------Prompt Template----------------------
template = """
You are a helpful assistant.
Answer ONLY from the provided transcript context and also mention the time given in brackets.
If the context is insufficient, just say you don't know.

Context:
{transcript}

Question: {question}
"""

prompt = PromptTemplate(
    input_variables=["transcript", "question"],
    template=template,
)
# ------------------ Structured Output Schema ------------------
class AnsandTime(BaseModel):
    answer: list[str] = Field(
        description="Answers to user's question (do NOT include timestamps here)"
    )
    timestamps: float = Field(
        description="The time (in seconds) from where the answer is taken"
    )

structured_model = model.with_structured_output(AnsandTime)

# ------------------ ChatState ------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], "add_messages"]

# ------------------ Chat Node ------------------
def chat_node(state: ChatState):
    # Extract user question from state
    user_message = state["messages"][-1].content  # last message is the user's input

    # Fill the prompt
    final_prompt = prompt.format(
        transcript=youtube_captions,   # <-- your transcript goes here
        question=user_message
    )

    # Get structured output
    response = structured_model.invoke(final_prompt)
    ai_text = f"Answer: {response.answer}\nTimestamp: {response.timestamps}"

    return {
        "messages": [
            state["messages"][-1],  # include the HumanMessage again
            AIMessage(content=ai_text)  # add the AI reply
        ]
    }

# ------------------ Build Graph ------------------
checkpointer = InMemorySaver()

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

CONFIG = {'configurable': {'thread_id': "newthread"}}
workflow =graph.compile(checkpointer = checkpointer)


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
# config
CONFIG = {'configurable': {'thread_id': "newthread"}}
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

    result = workflow.invoke(
        {'messages': [HumanMessage(content=user_input)]},
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

    print("AI:", output_dict['ai'])
print(output_dict)