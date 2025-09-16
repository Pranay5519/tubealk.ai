
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
load_dotenv()
#--------------------------
 # Utility Functions
#--------------------------
from youtube_transcript_api import YouTubeTranscriptApi
import re
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
from dataclasses import dataclass
@dataclass
class TimestampedSegment:
    """Represents a segment of transcript with timestamp"""
    text: str
    start_time: float
    end_time: float = None
    
def parse_transcript(transcript: str) -> List[TimestampedSegment]:

        segments = []
        
        # Regular expression to find text and timestamps
        # Pattern: captures text followed by timestamp in parentheses
        pattern = r'(.*?)\((\d+\.?\d*)\)'
        
        matches = re.findall(pattern, transcript)
        
        for i, (text, timestamp) in enumerate(matches):
            text = text.strip()
            if text:  # Only add non-empty text segments
                segment = TimestampedSegment(
                    text=text,
                    start_time=float(timestamp),
                    end_time=float(matches[i+1][1]) if i+1 < len(matches) else None
                )
                segments.append(segment)
        
        return segments

# -------------------------
# 1) Pydantic output schema
# -------------------------
class Subtopic(BaseModel):
    subtopic: str = Field(description="Short name or description of the subtopic")
    timestamp: float = Field(description="Approx timestamp in seconds where this subtopic is discussed")
    importance: Optional[str] = Field(default=None, description="Optional importance: high/medium/low")

class MainTopic(BaseModel):
    topic: str = Field(description="Main topic name or short description")
    timestamp: float = Field(description="Approx timestamp in seconds where the main topic starts")
    subtopics: List[Subtopic] = Field(description="List of subtopics under this main topic")

class TopicsOutput(BaseModel):
    main_topics: List[MainTopic] = Field(description="List of main topics with subtopics and timestamps")

# Create parser to enforce output JSON matches schema
parser = PydanticOutputParser(pydantic_object=TopicsOutput)
format_instructions = parser.get_format_instructions()

# -------------------------
# 2) System message prompt
# -------------------------
system_message = SystemMessagePromptTemplate.from_template(
    """You are an expert in analyzing and structuring video transcripts.

You will receive a transcript of a YouTube video with timestamps.

Your task is to:
1. Extract all MAIN TOPICS discussed in the transcript.
2. For each MAIN TOPIC, list its SUBTOPICS in a hierarchical structure.
3. Always include timestamp references (in seconds) for both MAIN TOPICS and SUBTOPICS.
4. For each subtopic, optionally add an 'importance' (high/medium/low) if it is clearly emphasized.
5. Be concise and only include material that is actually discussed in the transcript.
6. Output must be valid JSON and match the schema instructions below.

REQUIRED OUTPUT FORMAT:
{format_instructions}

Transcript (will be supplied by the user below).
"""
)

# ---------------------------------------
# 3) Human prompt (we supply the transcript)
# ---------------------------------------
human_message = HumanMessagePromptTemplate.from_template(
    """Transcript:
{transcript}

Notes:
- Use timestamps in seconds (floats allowed).
- Only include main topics and subtopics actually present in the transcript.
- If something is unclear, omit it rather than inventing timestamps.

Now extract main topics and subtopics."""
)

chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])

# -------------------------
# 4) Google 2.5 flash Modela
# -------------------------
# Make sure GOOGLE_APPLICATION_CREDENTIALS env var is set to your service account json file.
# The langchain VertexAI wrapper will pick up credentials automatically.
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
# -------------------------
# 5) Runner function
# -------------------------
def extract_topics_from_transcript(transcript: str) -> TopicsOutput:
    """
    transcript: the transcript text (should contain timestamps or speaker timestamps)
    returns: TopicsOutput (pydantic object) containing main_topics -> subtopics
    """
    # Build the prompt (the format_instructions are injected into system message already)
    prompt = chat_prompt.format_prompt(transcript=transcript, format_instructions=format_instructions)
    messages = prompt.to_messages()  # list of BaseMessage objects (system + human)

    # Call the VertexAI chat model
    # predict_messages returns a BaseMessage in many LangChain chat wrappers
    response_message = model.invoke(messages)

    # response_message.content contains the model's text output (expected JSON)
    raw_output = response_message.content

    # Parse into Pydantic model (this will raise if model output isn't valid JSON per schema)
   
    return raw_output,response_message

if __name__ == "__main__":
   
    captions = load_transcript("https://www.youtube.com/watch?v=fZM3oX4xEyg&t=1s")
    segments =parse_transcript(captions)
    formatted = []
    for segment in segments:
        formatted.append(f"[{segment.start_time}s] {segment.text}")
    
    raw_output , response_message = extract_topics_from_transcript(" ".join(formatted))
    #parser.parse(raw_output)
    # Nicely formatted display of main topics and subtopics
    for i, topics in enumerate(parser.parse(raw_output).main_topics, 1):
        print(f"\n🎯 Main Topic {i}: {topics.topic}  ⏰ {topics.timestamp}")
        print("----------------------------------------------------")

        for j, sub in enumerate(topics.subtopics, 1):
            print(f"   🔹 Subtopic {i}.{j}: {sub.subtopic}  ⏰ {sub.timestamp} {sub.importance}")

        print("====================================================")