# imports
from utility_functions import *
from testing_yt_rag import workflow
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage



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

    print("AI:", output_dict['ai'][-1])
