import streamlit as st
import re
from dotenv import load_dotenv

# Import all modules from testing folders
from langchain_core.messages import HumanMessage, AIMessage

# Chatbot imports
from testing_chatbot.rag.yt_rag_model import build_chatbot, retrieve_all_threads
from testing_chatbot.rag.utils_youtube import get_embed_url, load_transcript
from testing_chatbot.rag.utils_database import save_youtube_url_to_db, delete_all_threads_from_db, save_captions_to_db
from testing_chatbot.rag.utils_st_sessions import reset_chat, sidebar_thread_selection, add_threadId_to_chatThreads
from testing_chatbot.rag.utils_rag import text_splitter, generate_embeddings, retriever_docs, save_embeddings_faiss, clear_faiss_indexes

# Quiz imports
from testing_quiz.model_quiz import QuizGenerator
from testing_quiz.utils import save_quiz_to_db, load_quiz_from_db

# Summary imports
from testing_summary.test_model import generate_summary
from testing_summary.utlis_db import extract_topics_from_db, save_summary_to_db, get_summary_if_exists

# Topics imports
from testing_TopicsTimestamps.model import extract_topics_from_transcript, parse_transcript
from testing_TopicsTimestamps.utils_db import save_topics_to_db, load_topics_from_db

# Load environment variables
load_dotenv()

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="TubeTalk.ai - Learn Smarter",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CACHING FUNCTIONS
# =============================================================================
@st.cache_data(show_spinner=False)
def cached_load_transcript(url: str):
    """Cache YouTube transcript."""
    return load_transcript(url)

@st.cache_data(show_spinner=False)
def cached_text_splitter(captions: list):
    """Cache text splitting."""
    return text_splitter(captions)

@st.cache_resource(show_spinner=False)
def cached_generate_embeddings(_chunks: list):
    """Cache embeddings."""
    return generate_embeddings(_chunks)

@st.cache_resource(show_spinner=False)
def cached_retriever(_vector_store):
    """Cache retriever object."""
    return retriever_docs(_vector_store)

@st.cache_resource(show_spinner=False)
def cached_build_chatbot(retriever=None):
    return build_chatbot(retriever=retriever)

def clear_model_cache():
    """Clear cached chatbot, retriever, and embeddings."""
    cached_build_chatbot.clear()
    cached_retriever.clear()
    cached_generate_embeddings.clear()

@st.cache_data(show_spinner=True)
def get_transcript(url: str):
    captions = load_transcript(url)
    segments = parse_transcript(captions)
    return ["[" + str(s.start_time) + "s] " + s.text for s in segments]

@st.cache_data(show_spinner=True)
def get_topics_summary(formatted_text: str):
    return extract_topics_from_transcript(" ".join(formatted_text))

@st.cache_data
def get_captions(youtube_url: str):
    return load_transcript(youtube_url)

@st.cache_resource
def get_quiz(captions):
    quiz_gen = QuizGenerator()
    return quiz_gen.generate_quiz(captions)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

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

if "play_index" not in st.session_state:
    st.session_state.play_index = None

# =============================================================================
# CUSTOM CSS - FIXED LAYOUT
# =============================================================================
st.markdown("""
<style>
    /* Reset default Streamlit padding */
    .block-container {
        padding-top: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
    /* Main header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
    }
    
    .main-header h3 {
        color: white;
        margin: 0;
        font-weight: normal;
    }
    
    /* Feature cards */
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        color: black;
    }
    
    .feature-card h4 {
        color: #667eea;
        margin-top: 0;
    }
    
    /* Chat specific styles - only for LectureChat page */
    .chat-layout .fixed-video {
        position: fixed;
        top: 140px;
        right: 2vw;
        z-index: 100;
        background-color: white;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .chat-layout .chat-container {
        max-width: 50%;
        margin-left: 0;
    }
    
    /* Default content alignment */
    .content-container {
        max-width: 100%;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
st.sidebar.title("🎓 TubeTalk.ai")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate to:",
    ["🏠 Home", "📝 SmartSummary", "⏰ TimelineTopics", "💬 LectureChat", "🧠 KnowledgeQuiz"]
)

st.session_state.current_page = page.split(" ", 1)[1]

st.sidebar.markdown("---")
st.sidebar.info("Transform YouTube lectures into interactive learning experiences")

# =============================================================================
# HOME PAGE
# =============================================================================
if st.session_state.current_page == "Home":
    st.markdown("""
    <div class="main-header">
        <h1>🎓 Welcome to TubeTalk.ai</h1>
        <h3>Transform YouTube Lectures into Interactive Learning Experience</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ## 🎯 Why TubeTalk.ai?
        
        **Transform hours of YouTube lectures into structured learning experiences!**
        
        Most students learn from YouTube lectures that are 1+ hours long with no structured notes or navigation. 
        TubeTalk.ai solves this by providing AI-powered learning tools that make video lectures interactive and efficient.
        
        ### 🚀 Core Features:
        """)
        
        st.markdown("""
        <div class="feature-card">
            <h4>📝 SmartSummary</h4>
            <p>Get comprehensive lecture summaries and notes automatically generated from any YouTube lecture. 
            Perfect for quick review and study preparation.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>⏰ TimelineTopics</h4>
            <p>Navigate directly to specific topics with precise timestamps. 
            No more scrubbing through hour-long videos to find what you need!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>💬 LectureChat</h4>
            <p>Ask questions about the lecture content and get detailed answers with exact timestamp references. 
            It's like having a teaching assistant available 24/7!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>🧠 KnowledgeQuiz</h4>
            <p>Test your understanding with automatically generated quizzes based on lecture content. 
            Perfect for exam preparation and knowledge assessment.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🔧 Technology Stack")
        st.info("""
        **AI & ML:**
        - 🤖 Google Gemini 2.5 Flash
        - 🔗 LangChain/LangGraph
        - 📊 Vector Databases
        
        **Backend:**
        - 🐍 Python
        - ⚡ Flask/FastAPI
        - 🗄️ Database Storage
        
        **Features:**
        - 📋 Structured Output
        - 🎯 Precise Timestamps
        - 🔍 Semantic Search
        """)
    
    st.markdown("---")
    st.markdown("## 🔄 How TubeTalk.ai Works")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        ### 1️⃣ Paste Link
        Simply paste any YouTube lecture URL into TubeTalk.ai
        """)

    with col2:
        st.markdown("""
        ### 2️⃣ AI Analysis
        Our AI processes the video transcript using advanced NLP
        """)

    with col3:
        st.markdown("""
        ### 3️⃣ Smart Features
        Get summaries, timelines, chat, and quizzes instantly
        """)

    with col4:
        st.markdown("""
        ### 4️⃣ Learn Better
        Navigate, understand, and test your knowledge efficiently
        """)

    st.markdown("---")
    st.markdown("### 🚀 Ready to Transform Your Learning?")
    st.markdown("**👈 Select a feature from the sidebar** to see the magic in action!")

# =============================================================================
# SMART SUMMARY PAGE
# =============================================================================
elif st.session_state.current_page == "SmartSummary":
    st.title("📝 SmartSummary")
    st.write("Get comprehensive summaries from YouTube lecture transcripts.")
    
    url_input = st.text_input("🔗 Enter YouTube URL:", "")
    thread_id = st.text_input("🆔 Enter Thread ID:", "")
    
    if st.button("🔎 Generate Summary"):
        if not thread_id.strip():
            st.warning("⚠️ Please enter a Thread ID.")
        else:
            topics_text = extract_topics_from_db(thread_id)
            
            existing_summary = get_summary_if_exists(thread_id)
            if existing_summary:
                st.success("✅ Summary already exists for this thread!")
                st.subheader("📄 Saved Summary")
                st.write(existing_summary)
            else:
                transcript_text = ""
                if url_input.strip():
                    with st.spinner("Fetching transcript..."):
                        transcript_text = load_transcript(url_input)
                        if transcript_text is None:
                            st.error("❌ Could not fetch transcript for this video.")
                            transcript_text = ""
                        else:
                            st.success("✅ Transcript fetched successfully!")
                
                if not transcript_text.strip() or not topics_text.strip():
                    st.warning("⚠️ Please provide both transcript and topics/subtopics.")
                else:
                    with st.spinner("Generating summary..."):
                        summary = generate_summary(transcript_text, topics_text)
                        save_summary_to_db(thread_id, summary)
                    
                    st.subheader("✅ Summary")
                    st.write(summary)

# =============================================================================
# TIMELINE TOPICS PAGE
# =============================================================================
elif st.session_state.current_page == "TimelineTopics":
    st.title("⏰ TimelineTopics - Topics Extractor")
    
    youtube_url = st.text_input("Enter YouTube URL:")
    thread_id = st.text_input("Enter Thread ID:")
    
    if youtube_url and thread_id:
        output = load_topics_from_db(thread_id)
        if output:
            st.success("✅ Topics loaded from DB!")
        else:
            st.info("⏳ Fetching transcript...")
            formatted = get_transcript(youtube_url)
            output = get_topics_summary(formatted)
            save_topics_to_db(thread_id, output.model_dump_json())
            st.success("✅ Topics extracted & saved to DB!")
        
        embed_url = get_embed_url(youtube_url)
        st.subheader("📚 Extracted Topics")
        
        for i, topic in enumerate(output.main_topics, 1):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"🎯 **Main Topic {i}: {topic.topic}**")
            with col2:
                if st.button("▶️ Play", key=f"play_main_{i}"):
                    st.session_state.play_index = (f"main-{i}", topic.timestamp)
            
            with st.expander(f"🔽 Subtopics for: {topic.topic}"):
                for j, sub in enumerate(topic.subtopics, 1):
                    sub_col1, sub_col2 = st.columns([4, 1])
                    with sub_col1:
                        st.markdown(f"   🔹 **Subtopic {i}.{j}:** {sub.subtopic}")
                    with sub_col2:
                        if st.button("▶️ Play", key=f"play_sub_{i}_{j}"):
                            st.session_state.play_index = (f"sub-{i}-{j}", sub.timestamp)
        
        if st.session_state.play_index:
            label, timestamp = st.session_state.play_index
            start_time = int(float(timestamp))
            video_url = f"{embed_url}?start={start_time}&autoplay=1"
            st.markdown("---")
            st.subheader("📺 Video Player")
            st.markdown(f"""
            <iframe width="100%" height="450"
            src="{video_url}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
            encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
            </iframe>
            """, unsafe_allow_html=True)

# =============================================================================
# LECTURE CHAT PAGE
# =============================================================================
elif st.session_state.current_page == "LectureChat":
    st.markdown("""
    <div class="main-header">
        <h1>💬 LectureChat</h1>
        <p style="color: white; margin: 0;">Ask Questions, Get AI Answers with Timestamps</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar controls for chat
    st.sidebar.markdown("---")
    st.sidebar.title("🤖 Chat Controls")
    
    input_url = st.sidebar.text_input("Enter YouTube Video URL: ")
    thread_id_input = st.sidebar.text_input("Give a Conversation Name : ")
    
    database_url = None
    video_url = None
    retriever = None
    
    if st.sidebar.button("➕ Start New Chat", key="new_chat_btn"):
        clear_model_cache()
        if input_url and thread_id_input:
            reset_chat()
            database_url = None
            
            youtube_captions = cached_load_transcript(input_url)
            st.session_state.youtube_captions = youtube_captions
            st.session_state['youtube_url'] = input_url
            st.session_state['embed_url'] = []
            st.session_state['thread_id'] = []
            st.session_state.retriever = None
            st.success("✅ New chat started!")
        elif not input_url:
            st.warning("Please enter a YouTube URL before starting a new chat.")
        elif not thread_id_input:
            st.warning("Please enter a Conversation Name before starting a new chat.")
    
    if st.sidebar.button("🚮 Delete Conversations"):
        delete_all_threads_from_db()
        clear_faiss_indexes()
        st.success("✅ All conversations deleted!")
    
    youtube_captions = st.session_state['youtube_captions']
    
    if youtube_captions:
        status_box = st.empty()
        
        with st.spinner("⏳ Processing..."):
            status_box.info("🔄 Splitting text into chunks...")
            chunks = cached_text_splitter(youtube_captions)
            
            status_box.info("✅ Text split into chunks\n\n🔄 Generating embeddings...")
            vector_store = cached_generate_embeddings(chunks)
            
            status_box.info("✅ Embeddings generated\n\n🔄 Creating retriever...")
            retriever = cached_retriever(vector_store)
        
        status_box.success("🎉 Chatbot ready!")
    
    st.sidebar.markdown("---")
    st.sidebar.header("📂 My Conversations")
    
    chatbot = build_chatbot(retriever=retriever)
    sidebar_thread_selection(chatbot)
    
    if "retriever" in st.session_state and st.session_state['retriever']:
        chatbot = st.session_state['chatbot']
    else:
        chatbot = build_chatbot(retriever=retriever)
    
    if st.session_state['thread_id']:
        database_url = st.session_state['youtube_url']
    elif thread_id_input and input_url:
        video_url = input_url
    else:
        video_url = None
    
    # Layout: Chat on left, video on right
    col_chat, col_video = st.columns([1, 1])
    
    with col_chat:
        st.subheader("💬 Chat")
        
        # Display chat history
        for idx, message in enumerate(st.session_state["message_history"]):
            with st.chat_message(message["role"]):
                if message["role"] == 'assistant':
                    response_text, timestamp = map(str.strip, message['content'].split("Timestamp:"))
                    st.text(response_text)
                    
                    if st.button("▶️ Watch", key=f"watch_{idx}"):
                        st.session_state.play_index = ("chat", timestamp)
                else:
                    st.text(message["content"])
        
        # Chat input
        user_input = st.chat_input("Enter your question:")
        if user_input:
            if st.session_state['message_history'] == []:
                add_threadId_to_chatThreads(thread_id=thread_id_input)
                with st.spinner("saving into FAISS"):
                    save_embeddings_faiss(thread_id=thread_id_input, vector_store=vector_store)
                    save_youtube_url_to_db(thread_id=thread_id_input, youtube_url=input_url)
                    save_captions_to_db(thread_id=thread_id_input, captions=youtube_captions)
            
            st.session_state['message_history'].append({"role": "user", "content": user_input})
            
            CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
            
            if st.session_state['youtube_url'] == []:
                extract_url = input_url
            else:
                extract_url = st.session_state['youtube_url']
            
            response = "".join(
                chunk.content for chunk, _ in chatbot.stream(
                    {'messages': [HumanMessage(content=user_input)]},
                    config=CONFIG,
                    stream_mode='messages'
                )
            )
            
            st.session_state['message_history'].append({
                "role": "assistant",
                "content": response
            })
            
            st.rerun()
    
    with col_video:
        st.subheader("📺 Video Player")
        
        if database_url:
            embed_url = get_embed_url(database_url)
            
            # Check if we need to jump to timestamp
            if st.session_state.play_index and st.session_state.play_index[0] == "chat":
                timestamp = st.session_state.play_index[1]
                video_url_with_time = f"{embed_url}?start={int(float(timestamp))}&autoplay=1"
                st.session_state.play_index = None  # Reset
            else:
                video_url_with_time = embed_url
            
            st.markdown(f"""
            <iframe width="100%" height="500"
            src="{video_url_with_time}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
            encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
            </iframe>
            """, unsafe_allow_html=True)
        else:
            st.info("👈 Start a new chat to load the video player")

# =============================================================================
# KNOWLEDGE QUIZ PAGE
# =============================================================================
elif st.session_state.current_page == "KnowledgeQuiz":
    st.title("🧠 KnowledgeQuiz")
    
    youtube_url = st.text_input("Enter YouTube URL:")
    thread_id = st.text_input("Enter Thread ID:")
    
    embed_url = get_embed_url(youtube_url)
    
    if thread_id and youtube_url:
        quiz_list = load_quiz_from_db(thread_id)
        if quiz_list:
            st.success("✅ Quiz loaded from DB!")
        else:
            st.info("⏳ Generating quiz...")
            captions = get_captions(youtube_url)
            
            if captions:
                quiz_list = get_quiz(captions)
                save_quiz_to_db(thread_id, quiz_list.model_dump_json())
                st.success("✅ Quiz generated! and Saved to DB!")
        
        if "play_index" not in st.session_state:
            st.session_state.play_index = None
        
        for i, quiz in enumerate(quiz_list.quizzes, 1):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### Question {i}: {quiz.question}")
            
            user_answer = st.radio(
                f"Choose your answer for Question {i}",
                quiz.options,
                key=f"q{i}",
                index=None
            )
            
            with col2:
                if st.button("▶️ Play", key=f"play_q_{i}"):
                    st.session_state.play_index = (f"quiz-{i}", quiz.timestamp)
            
            if user_answer is not None:
                if user_answer == quiz.correct_answer:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Wrong! Correct answer is: {quiz.correct_answer}")
            
            st.markdown("---")
        
        if st.session_state.play_index:
            label, timestamp = st.session_state.play_index
            start_time = int(float(timestamp))
            video_url = f"{embed_url}?start={start_time}&autoplay=0"
            st.markdown("---")
            st.subheader("📺 Video Player")
            st.markdown(f"""
            <iframe width="100%" height="450"
            src="{video_url}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
            encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
            </iframe>
            """, unsafe_allow_html=True)
    else:
        st.info("👆 Enter YouTube URL and Thread ID to start the quiz")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Built with ❤️ using LangChain, Google Gemini AI, and Streamlit</p>
    <p>© 2024 TubeTalk.ai - Transform Your Learning Experience</p>
</div>
""", unsafe_allow_html=True)