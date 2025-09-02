import streamlit as st

st.set_page_config(
    page_title="TubeTalk.ai - Learn Smarter",
    page_icon="🎓",
    layout="wide"
)
#Hide Sidebar Home and other pages/files from displaying
hide_pages_style = """
<style>
[data-testid="stSidebarNav"] {display: none;}
</style>
"""
st.markdown(hide_pages_style, unsafe_allow_html=True)
# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        color: black;
    }
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
    }
    .stat-item {
        text-align: center;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🎓 Welcome to TubeTalk.ai</h1>
    <h3>Transform YouTube Lectures into Interactive Learning Experience</h3>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.success("🚀 Select a feature to explore")
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Quick Navigation")

if st.sidebar.button("📝 SmartSummary"):
    st.switch_page("pages/smartsummary.py")

if st.sidebar.button("⏰ TimelineTopics"):
    st.switch_page("pages/timelinetopics.py")

if st.sidebar.button("💬 LectureChat"):
    st.switch_page("pages/chatbot.py")  # <-- your chatbot page

if st.sidebar.button("🧠 KnowledgeQuiz"):
    st.switch_page("pages/knowledgequiz.py")

if st.sidebar.button("🎯 ConceptJump"):
    st.switch_page("pages/conceptjump.py")

# Main Content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## 🎯 Why TubeTalk.ai?
    
    **Transform hours of YouTube lectures into structured learning experiences!**
    
    Most students learn from YouTube lectures that are 1+ hours long with no structured notes or navigation. 
    TubeTalk.ai solves this by providing AI-powered learning tools that make video lectures interactive and efficient.
    
    ### 🚀 Core Features:
    """)
    
    # Feature Cards
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
    
    st.markdown("""
    <div class="feature-card">
        <h4>🎯 ConceptJump</h4>
        <p>Find exactly when specific concepts are introduced in the lecture. 
        Jump directly to "Machine Learning basics" or "Neural Networks" instantly!</p>
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
    
    
# How It Works Section
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

# Footer
st.markdown("---")
st.markdown("### 🚀 Ready to Transform Your Learning?")
st.markdown("""
TubeTalk.ai makes YouTube lectures interactive, searchable, and much more effective for learning. 
**👈 Select a feature from the sidebar** to see the magic in action!

### 💡 Perfect For:
- 📚 **Students** preparing for exams
- 🎓 **Researchers** reviewing conference talks  
- 💼 **Professionals** learning new skills
- 👨‍🏫 **Educators** creating course materials

### 🌟 Why Choose TubeTalk.ai?
- ⚡ **Instant Processing** - Get results in seconds
- 🎯 **Precise Timestamps** - Jump to exact moments  
- 🧠 **AI-Powered** - Powered by Google Gemini 2.5 Flash
- 📱 **Easy to Use** - Simple, intuitive interface

---
*Built with ❤️ using LangChain, Google Gemini AI, and modern web technologies*
""")