import streamlit as st
from model_quiz import QuizGenerator, load_transcript
from utils import get_embed_url , save_quiz_to_db ,load_quiz_from_db
st.title("📹 TubeTalk.ai → Topics Extractor")

youtube_url = st.text_input("Enter YouTube URL:")
thread_id = st.text_input("Enter a unique Thread ID (for saving & retrieving):")

# ✅ Cache transcript loading
@st.cache_data
def get_captions(youtube_url: str):
    return load_transcript(youtube_url)

# ✅ Cache quiz generation
@st.cache_resource
def get_quiz(captions):
    quiz_gen = QuizGenerator()
    return quiz_gen.generate_quiz(captions)

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
            save_quiz_to_db(thread_id,quiz_list.model_dump_json())  # Save to DB
            st.success("✅ Quiz generated! and Saved to DB!")
    if "play_index" not in st.session_state:
        st.session_state.play_index = None
    for i, quiz in enumerate(quiz_list.quizzes, 1):
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown(f"### Question {i}: {quiz.question}")
        
        # Radio button for answer options with NO preselection
        user_answer = st.radio(
            f"Choose your answer for Question {i}",
            quiz.options,
            key=f"q{i}",
            index=None   # 👈 ensures nothing is selected at start
        )
        with col2:
            if st.button("▶️ Play", key=f"play_q_{i}"):
                st.session_state.play_index = (f"quiz-{i}", quiz.timestamp)
                print(st.session_state.play_index)
        # Show correctness only after user clicks
        if user_answer is not None:
            if user_answer == quiz.correct_answer:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Wrong! Correct answer is: {quiz.correct_answer}")

        #st.markdown(f"*Timestamp:* {quiz.timestamp} seconds")
        st.markdown("---")
    if st.session_state.play_index:
        label, timestamp = st.session_state.play_index
        start_time = int(float(timestamp))
        video_url = f"{embed_url}?start={start_time}&autoplay=0"
        st.markdown(f"""
        
            <iframe width="800" height="450"
            src="{video_url}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
            encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
            </iframe>
        
        """, unsafe_allow_html=True)
    else:
        st.error("❌ Failed to fetch transcript. Please check the YouTube URL.")
