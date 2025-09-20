# test_model.py
import re
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

# -----------------------
# 1) Transcript Loader
# -----------------------
def load_transcript(url: str) -> str | None:
    """
    Fetch transcript for a YouTube video.
    """
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    if match:
        video_id = match.group(1)
        try:
            captions = YouTubeTranscriptApi().fetch(video_id, languages=['en','hi']).snippets
            data = [f"{item.text} ({item.start})" for item in captions]
            return " ".join(data)
        except Exception as e:
            print(f"❌ Error fetching transcript: {e}")
            return None
    return None

# -----------------------
# 2) Initialize LLM
# -----------------------
def get_summarizer_chain():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

    # Prompt template
    system_message = (
        "You are an expert video summarizer. Your task is to read the provided YouTube video transcript "
        "and the list of topics/subtopics, then create a clear, concise, and well-structured summary. "
        "⚠️ Important: Do NOT add or invent any information that is not present in the transcript. "
        "Only summarize the content given. Highlight the main ideas and key points under each topic, "
        "and remove filler or repetitive text. The output should be easy to understand, organized, "
        "and suitable for quick learning or revision."
    )

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "Transcript:\n{transcript}\n\nTopics & Subtopics:\n{topics}"),
    ])


    summarizer_chain = LLMChain(llm=llm, prompt=prompt)
    return summarizer_chain

# -----------------------
# 3) Generate Summary
# -----------------------
def generate_summary(transcript: str, topics: str) -> str:
    chain = get_summarizer_chain()
    return chain.run({"transcript": transcript, "topics": topics})
