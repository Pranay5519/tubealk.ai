
from testing_summary.model_langChain import YouTubeVideoSummarizer
from testing_quiz.model_quiz import QuizGenerator
from testing_chatbot.rag.utils_youtube import load_transcript
from typing import Tuple
from langchain_core.messages.ai import AIMessage
class ModelCalling:
    def __init__(self):
        pass
    
    def generate_summary(self, url: str) -> Tuple[AIMessage, "VideoSummary", dict]:
        transcripts = load_transcript(url=url)
        summarizer = YouTubeVideoSummarizer()
        response, parsed_output, summary = summarizer.summarize_video(transcripts)
        return response, parsed_output, summary
    
    def generate_quiz(self , url : str) :
        transcripts = load_transcript(url=url)
        quiz_gen = QuizGenerator()
        response = quiz_gen.generate_quiz(transcripts)
        return response
    