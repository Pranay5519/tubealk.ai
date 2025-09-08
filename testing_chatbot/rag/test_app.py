import streamlit as st
from langchain_core.messages import HumanMessage , AIMessage
from yt_rag_model import build_chatbot , retrieve_all_threads  
from testing_chatbot.rag.utils_youtube import get_embed_url , load_transcript
from testing_chatbot.rag.utils_database import  save_youtube_url_to_db , delete_all_threads_from_db
from testing_chatbot.rag.utils_st_sessions import reset_chat , sidebar_thread_selection , add_threadId_to_chatThreads
from testing_chatbot.rag.utils_rag import text_splitter , generate_embeddings , retriever_docs , save_embeddings_faiss ,clear_faiss_indexes
st.set_page_config(
    page_title="LectureChat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = []

if "chat_threads" not in st.session_state:
    st.session_state.chat_threads = retrieve_all_threads()

if "youtube_captions" not in st.session_state:
    st.session_state.youtube_captions = []
   
if "youtube_url" not in st.session_state:
    st.session_state.youtube_url = [] 
   
if "embed_url" not in st.session_state:
    st.session_state.embed_url = [] 
if "retriever" not in st.session_state:
    st.session_state.retriever = None 
# =============================================================================
# STYLING AND CSS
# =============================================================================
st.markdown("""
<div class="main-header">
    <div class="header-content">
        <h1>💬 LectureChat</h1>
        <p>Ask Questions, Get AI Answers with Timestamps</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* Header Styling */
    .main-header {
        background-color: #f0f2f6;
        border: 1px solid #e1e5e9;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .header-content h1 {
        color: #1f2937;
        margin-bottom: 5px;
    }
    
    .header-content p {
        color: #6b7280;
        margin: 0;
    }

    /* Fixed Video Position - Same as Original */
    .fixed-video {
        position: fixed;
        top: 140px;
        left: 2vw;
        z-index: 100;
        background-color: white;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* Chat Area - Same Layout as Original */
    .block-container {
        padding-top: 120px !important;
        max-width: 700px;
        margin-left: auto;
        margin-right: 2vw;
    }
    
    .stChatInput {
        max-width: 500px;
        margin-left: auto;
        margin-right: 5vw;
    }
    h3 {
    position: fixed;      /* lock it in place */
    top: 80px;           /* below header */
    left: 16vw;            /* move a bit right */
    font-size: 20px;
    font-weight: 600;
    margin: 0;
    background: none;     /* remove box */
    padding: 0;           /* no padding */
    box-shadow: none;     /* no shadow */
    color: #222;          /* dark text for visibility */
    z-index: 950;

    /* Spacer */
    .spacer {
        margin-top: 180px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR CONFIGURATION
# =============================================================================

st.sidebar.title("🤖LangGraph Chatbot with Gemini")
st.sidebar.success("🚀 Start your interactive lecture chat")

input_url = st.sidebar.text_input("Enter YouTube Video URL: ")
thread_id = st.sidebar.text_input("Give a Conversation Name : ")

# define Variables 
database_url = None
video_url = None
# =============================================================================
# MAIN CONTENT AREA - THREAD AND VIDEO DISPLAY
# =============================================================================

# Show thread id on Top (if exists)
print(">>> Checking Thread and Video display section")
print("Thread_Id :" , st.session_state['thread_id'])

# =============================================================================
# SIDEBAR FUNCTIONALITY - NEW CHAT BUTTON
# =============================================================================
retriever = None
if st.sidebar.button("➕ Start New Chat", key="new_chat_btn"):
    if input_url and thread_id:  # only load transcript if URL is provided
        reset_chat()  # clear old chat first
        database_url = None
        
        youtube_captions = load_transcript(input_url)
        st.session_state.youtube_captions = youtube_captions
        st.session_state['youtube_url'] = input_url
        st.session_state['embed_url'] = []
        st.session_state['thread_id'] = []
        st.session_state.retriever = None 
        st.subheader(thread_id)
        print("Displaying YouTube video from Input")
        embed_url = get_embed_url(input_url)
        st.markdown(f"""
            <div class="fixed-video">
                <iframe width="800" height="400"
                src="{embed_url}"
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
                encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                </iframe>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif not input_url:
        st.warning("Please enter a YouTube URL before starting a new chat.")
    elif not thread_id:
         st.warning("Please enter a Conversation Name before starting a new chat.")

# =============================================================================
# SIDEBAR - CONVERSATION HISTORY
# =============================================================================
print("-" * 30)
if st.sidebar.button("🚮 Delete Conversations"):
    delete_all_threads_from_db()
    clear_faiss_indexes()

youtube_captions = st.session_state['youtube_captions']

if youtube_captions:
    status_box = st.empty()  # placeholder for single updating message

    with st.spinner("⏳ Processing..."):
        status_box.info("🔄 Splitting text into chunks...")
        chunks = text_splitter(youtube_captions)

        status_box.info("✅ Text split into chunks\n\n🔄 Generating embeddings...")
        vector_store = generate_embeddings(chunks)

        status_box.info("✅ Embeddings generated\n\n🔄 Creating retriever...")
        retriever = retriever_docs(vector_store)

    status_box.success("🎉 Chatbot ready!")

st.sidebar.markdown("---")
st.sidebar.header("📂 My Conversations")
        
chatbot = build_chatbot(retriever=retriever)
sidebar_thread_selection(chatbot)
# Use retriever from session state if available
if "retriever" in st.session_state and st.session_state['retriever']:
    chatbot = st.session_state['chatbot']
else:
    chatbot = build_chatbot(retriever=retriever)


# Show saved YouTube video (if exists)

if st.session_state['thread_id']:
    database_url = st.session_state['youtube_url']
    print("Loading video from session DataBase URL-->" , database_url)
elif thread_id and input_url:
    print("Loading  video URL INPUT ")
    video_url = input_url
else:
    print("No video URL found")
    video_url = None


if database_url:
    
    embed_url = get_embed_url(database_url)
    st.markdown(f"""
        <div class="fixed-video">
            <iframe width="800" height="400"
            src="{embed_url}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
            encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
            </iframe>
        </div>
        """,
        unsafe_allow_html=True
    ) 
    print("Displaying YouTube video from DataBase")


# =============================================================================
# CHAT DISPLAY AND INTERACTION
# =============================================================================

# Display Chat History
for idx, message in enumerate(st.session_state["message_history"]):
    with st.chat_message(message["role"]):
        if message["role"] == 'assistant':
            response_text, timestamp = map(str.strip, message['content'].split("Timestamp:"))
            st.text(response_text)
            #print("youtube_url_history_load-->" , st.session_state['youtube_url'])
            url = get_embed_url(st.session_state['youtube_url'])
            
            timestamp_url_play = f"{url}?start={int(float(timestamp))}&autoplay=1"

            # unique key using idx
            if st.button("▶️ Watch", key=f"watch_{idx}"):
                print(f"Watch button clicked From Message History {idx} - ▶️")
                st.markdown(
                    f"""
                    <div class="fixed-video">
                        <iframe width="800" height="400"
                        src="{timestamp_url_play}"
                        frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
                        encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                        </iframe>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:
            st.text(message["content"])


# Chat Input Processing
user_input = st.chat_input("Enter your question:")
if user_input:   
    if st.session_state['message_history'] == []:
        add_threadId_to_chatThreads(thread_id=thread_id)
        with st.spinner("saving into FAISS"):
            save_embeddings_faiss(thread_id=thread_id ,vector_store=vector_store)   
            save_youtube_url_to_db(thread_id=thread_id , youtube_url=input_url )
        st.sidebar.status("Done") 
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    youtube_captions = st.session_state['youtube_captions']
    
    if st.session_state['youtube_url'] == []: # extract url is from user input url
        extract_url = input_url
    else:
        extract_url = st.session_state['youtube_url']
        
    

    with st.chat_message("assistant"):
        response = "".join(
            chunk.content for chunk,_ in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )
        print("AI : " , response)
        response_text, timestamp = map(str.strip, response.split("Timestamp:"))
        st.write(response_text)
        timestamp_url = f"{extract_url}&t={int(float(timestamp))}s"
        print("Extract url", extract_url)
        print("video URL:", video_url)
        
        embed_url = get_embed_url(extract_url)
        timestamp_url_play = f"{embed_url}?start={int(float(timestamp))}&autoplay=1"
        
        #print("EMbede URL:", embed_url)
        #print("TIMESTAMP URL:", timestamp_url)
        #print("TIMESTAMP URL:", timestamp_url_play)
        #print("--" * 50)
        
        #st.session_state['embed_url'] = timestamp_url_play
        
    
    st.session_state['message_history'].append({
            "role": "assistant",
            "content": response
        })

    st.rerun()
print("=" * 80)