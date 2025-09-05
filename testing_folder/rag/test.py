from langchain_core.messages import HumanMessage
from testing_folder.rag.yt_rag_model import *
from testing_folder.non_rag.utility_functions import *
# ------------------ Config ------------------
thread_id = "thread2"
BASE_CONFIG = {"configurable": {"thread_id": thread_id}}
youtube_input = "https://www.youtube.com/watch?v=s3KnSb9b4Pk&t"
youtube_captions = load_transcript(youtube_input)
chunks = text_splitter(youtube_captions)
vector_store = generate_embeddings(chunks)
retriever = retriever_docs(vector_store)
print("Setup Ready")
# ------------------ Transcript + Embeddings ------------------
youtube_captions = load_transcript(youtube_input)

chatbot = build_chatbot(retriever=retriever)
# ------------------ Chat Loop ------------------
while True:
    user_input = input("User: ")
    if user_input.lower() == "exit":
        break

    result = chatbot.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config={**BASE_CONFIG, "retriever": retriever},   # ✅ pass retriever here
    )

    print("AI:", result["messages"][-1].content)

