import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
load_dotenv()

import re 
from youtube_transcript_api import YouTubeTranscriptApi
def load_transcript(url: str) -> str | None:
    """
    Fetch transcript for a YouTube video.
    """
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    if match:
        video_id = match.group(1)
        try:
            captions = YouTubeTranscriptApi().fetch(video_id,languages=['en','hi']).snippets
            data = [f"{item.text} ({item.start})" for item in captions]
            return " ".join(data)
        except Exception as e:
            print(f"❌ Error fetching transcript: {e}")
            return None

# Streamlit page setup
st.set_page_config(page_title="YouTube Transcript Summarizer", layout="centered")

st.title("🎬 YouTube Transcript Summarizer")
st.write("Paste the transcript and topics/subtopics, and get a clean summary.")

# Input fields
url_input= st.text_input("🔗 Enter YouTube URL (to fetch transcript automatically)", "") 
topics_text = st.text_area("📌 Enter Topics & Subtopics", height=150, placeholder="List of topics/subtopics...")
transcript_text = load_transcript(url_input)
# Initialize Gemini model (Google 2.5 Flash)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3
)

# Proper System Message
system_message = (
    "You are an expert video summarizer. Your task is to read the provided "
    "YouTube video transcript and the list of topics/subtopics, then create a "
    "clear, concise, and well-structured summary. Highlight the main ideas, key "
    "points under each topic, and remove filler or repetitive text. The output "
    "should be easy to understand, organized, and suitable for quick learning or revision."
)

# Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    ("human", "Transcript:\n{transcript}\n\nTopics & Subtopics:\n{topics}")
])

# Chain
summarizer_chain = LLMChain(
    llm=llm,
    prompt=prompt
)

# Button action
if st.button("🔎 Generate Summary"):
    if transcript_text.strip() == "" or topics_text.strip() == "":
        st.warning("⚠️ Please enter both transcript and topics/subtopics.")
    else:
        with st.spinner("Generating summary..."):
            summary = summarizer_chain.run({
                "transcript": transcript_text,
                "topics": topics_text
            })
        st.subheader("✅ Summary")
        st.write(summary)
