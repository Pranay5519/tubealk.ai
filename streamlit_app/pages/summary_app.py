# test_app.py
import streamlit as st
from dotenv import load_dotenv
from testing_summary.test_model import load_transcript, generate_summary
from testing_summary.utlis_db import extract_topics_from_db , save_summary_to_db ,get_summary_if_exists
# Load environment variables (Google credentials etc.)
load_dotenv()

# -----------------------
# Streamlit page setup
# -----------------------
st.set_page_config(page_title="TubeTalk.ai Summarizer", layout="centered")

st.title("🎬TubeTalk.ai Summarizer")
st.write("Paste the transcript and topics/subtopics, and get a clean summary.")

# -----------------------
# Input fields
# -----------------------
url_input = st.text_input("🔗 Enter YouTube URL (to fetch transcript automatically)", "")
thread_id = st.text_input("🆔 Enter a unique Thread ID (for saving & retrieving)", "")



# -----------------------
# Button action
# -----------------------
if st.button("🔎 Generate Summary"):
    if not thread_id.strip():
        st.warning("⚠️ Please enter a Thread ID.")
    else:
        topics_text = extract_topics_from_db(thread_id)  # make sure this returns a string
        print(topics_text)
        # 1️⃣ Check if summary already exists
        existing_summary = get_summary_if_exists(thread_id)
        if existing_summary:
            st.success("✅ Summary already exists for this thread!")
            st.subheader("📄 Saved Summary")
            st.write(existing_summary)
        else:
            # 2️⃣ Fetch transcript if URL is provided
            transcript_text = ""
            if url_input.strip():
                with st.spinner("Fetching transcript..."):
                    transcript_text = load_transcript(url_input)
                    if transcript_text is None:
                        st.error("❌ Could not fetch transcript for this video.")
                        transcript_text = ""
                    else:
                        st.success("✅ Transcript fetched successfully!")
            
            # 3️⃣ Load topics from DB (or wherever your function fetches them)
            
            
            # 4️⃣ Validate inputs before generating summary
            if not transcript_text.strip() or not topics_text.strip():
                st.warning("⚠️ Please provide both transcript and topics/subtopics.")
            else:
                # 5️⃣ Generate summary and save to DB
                with st.spinner("Generating summary..."):
                    summary = generate_summary(transcript_text, topics_text)
                    save_summary_to_db(thread_id, summary)  # Save summary to DB
                
                st.subheader("✅ Summary")
                st.write(summary)


