import re
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain.llms import OpenAI

from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import BaseOutputParser
from pydantic import BaseModel, Field
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()

@dataclass
class TimestampedSegment:
    """Represents a segment of transcript with timestamp"""
    text: str
    start_time: float
    end_time: float = None

class SummaryPoint(BaseModel):
    """Individual summary point with timestamp reference"""
    content: str = Field(description="The main point or topic discussed")
    timestamp: float = Field(description="Timestamp in seconds when this topic was discussed")
    importance: str = Field(description="Importance level: high, medium, low")

class BriefSummary(BaseModel):
    key_points: List[SummaryPoint] = Field(description="List of key points with timestamps and also inlcudes brief summary on Each key Point , does not include unimportant topics")

class MainTopic(BaseModel):
    topic: str = Field(description="The topic name")
    timestamp: float = Field(description="Approx timestamp when topic starts")

class VideoSummary(BaseModel):
    """Complete video summary structure"""
    title: str = Field(description="Suggested title for the video based on content")
    overview: str = Field(description="Brief overview of the entire video upto 200 words")
    key_pt_brief_summary : List[BriefSummary] = Field(description="Brief Summary for each Key Point")
    main_topics: List[MainTopic] = Field(description="List of main topics covered")
    duration_summary: str = Field(description="Summary of video duration and pacing")

class YouTubeVideoSummarizer:
    def __init__(self):
        """
        Initialize the summarizer with OpenAI API key
        
        Args:
            api_key: OpenAI API key
            model_name: Model to use for summarization
        """
        self.llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.3
    )
        self.output_parser = PydanticOutputParser(pydantic_object=VideoSummary)
    
    def parse_transcript(self, transcript: str) -> List[TimestampedSegment]:
        """
        Parse transcript text with timestamps in format:
        "text content (timestamp) more text (timestamp)"
        
        Args:
            transcript: Raw transcript string
            
        Returns:
            List of TimestampedSegment objects
        """
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
    
    def format_transcript_for_llm(self, segments: List[TimestampedSegment]) -> str:
        """
        Format parsed segments for LLM processing
        
        Args:
            segments: List of timestamped segments
            
        Returns:
            Formatted transcript string
        """
        formatted_parts = []
        
        for segment in segments:
            timestamp_str = f"[{segment.start_time}s]"
            formatted_parts.append(f"{timestamp_str} {segment.text}")
        
        return "\n".join(formatted_parts)
    
    def create_summary_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for video summarization"""
        
        system_message = SystemMessagePromptTemplate.from_template(
            """You are an expert video content analyzer and summarizer. 
            You will receive a transcript of a YouTube video with timestamps.
            
            Your task is to:
            1. Create a structured summary with key points
            2. Include timestamp references for each point
            3. Identify main topics and themes
            4. Provide an overall assessment of the video content
            
            Be concise but comprehensive. Focus on the most important information.
            Always include the timestamp reference for where you found each piece of information.
            
            {format_instructions}
            """
        )
        
        human_message = HumanMessagePromptTemplate.from_template(
            """Please analyze and summarize the following timestamped video transcript:

            {transcript}
            
            Provide a structured summary following the specified format.
            """
        )
        
        return ChatPromptTemplate.from_messages([system_message, human_message])
    
    def summarize_video(self, transcript: str) -> Dict[str, Any]:
        """
        Main method to summarize a video transcript
        
        Args:
            transcript: Raw transcript string with timestamps
            
        Returns:
            Structured summary dictionary
        """
        # Parse the transcript
        segments = self.parse_transcript(transcript)
        
        if not segments:
            return {"error": "No valid transcript segments found"}
        
        # Format for LLM
        formatted_transcript = self.format_transcript_for_llm(segments)
        
        # Create prompt
        prompt = self.create_summary_prompt()
        
        # Prepare the input
        formatted_prompt = prompt.format_prompt(
            transcript=formatted_transcript,
            format_instructions=self.output_parser.get_format_instructions()
        )
        
        # Generate summary
        try:
            response = self.llm(formatted_prompt.to_messages())
            parsed_output = self.output_parser.parse(response.content)
            
            # Convert to dictionary and add metadata
            summary_dict = parsed_output.dict()
            summary_dict["total_segments"] = len(segments)
            summary_dict["video_duration"] = max([s.start_time for s in segments]) if segments else 0
            
            return response , parsed_output , summary_dict
            
        except Exception as e:
            return {"error": f"Failed to generate summary: {str(e)}"}
    
    def format_summary_output(summary: Dict[str, Any]) -> str:
        if "error" in summary:
            return f"Error: {summary['error']}"
        
        output = []
        output.append(f"📹 VIDEO SUMMARY")
        output.append("=" * 50)
        output.append(f"Title: {summary['title']}")
        output.append(f"Duration: {summary.get('video_duration', 0):.1f} seconds")
        output.append(f"Total Segments: {summary.get('total_segments', 0)}")
        output.append("")
        
        output.append("📚 MAIN TOPICS:")
        for topic in summary['main_topics']:
            output.append(f"• {topic['topic']}\t")
            output.append(f"{topic['timestamp']}")
        output.append("")
        
        output.append("📋 OVERVIEW:")
        output.append(summary['overview'])
        output.append("")
        
        output.append("🎯 KEY POINTS:")
        for i, point in enumerate(summary['key_pt_brief_summary'][0]['key_points'],1):
            output.append(f"{i}. {point['content']}")
            output.append(f"   ⏰ Timestamp: {point['timestamp']}s | Importance: {point['importance']}")
            output.append("")
        
        output.append("⏱️ PACING ANALYSIS:")
        output.append(summary['duration_summary'])
        
        return "\n".join(output)
    