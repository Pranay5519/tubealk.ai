from langchain_google_genai import ChatGoogleGenerativeAI
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel, Field
from typing import List
#rom testing_chatbot.rag.utils_youtube import load_transcript
import re
from dotenv import load_dotenv
load_dotenv()
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

class Quiz(BaseModel):
    question: str = Field(description="A well-formed multiple-choice quiz question")
    options: List[str] = Field(description="List of 4 possible answer options")
    correct_answer: str = Field(description="The correct answer from the options list")
    timestamp : float = Field(description="timestamp from where the quesiton was picked from the transcripts")
class QuizList(BaseModel):
    quizzes: List[Quiz] = Field(description="List of 10 quiz questions with options and answers")

class QuizGenerator:
    def __init__(self):
        pass
    
    def generate_quiz(self,transcripts : str):
        system_template = """You are QuizBot, an AI assistant that creates professional quizzes.
        Your task is to generate exactly 10 multiple-choice questions from the provided YouTube transcript.
        Each question must:
        - Be clear, concise, and relevant to the transcript content
        - Include 4 answer options (A, B, C, D)
        - Clearly specify the correct answer
        Format the response strictly as structured data according to the schema provided.
        Do not include explanations, context, or additional text outside the schema.
        """

        user_template = """
        Here is the YouTube video transcript:
        {transcript}
        """
        quiz_prompt = ChatPromptTemplate.from_messages([
                        SystemMessagePromptTemplate.from_template(system_template),
                        HumanMessagePromptTemplate.from_template(user_template),
                    ])
        
        model = ChatGoogleGenerativeAI(model = 'gemini-2.5-flash' , temperature=0)
        structured_llm = model.with_structured_output(QuizList)

        response = structured_llm.invoke(
            quiz_prompt.format_prompt(transcript=transcripts).to_messages()
        )
        return response
    
    
if __name__ == "__main__":
    # Load transcript
    captions = load_transcript("https://www.youtube.com/watch?v=s3KnSb9b4Pk")

    # Initialize quiz generator
    quiz_gen = QuizGenerator()

    # Generate quizzes
    response = quiz_gen.generate_quiz(captions)

    # Print quizzes
    for idx, quiz in enumerate(response.quizzes, 1):
        print(f"Q{idx}: {quiz.question}")
        print("Options:", quiz.options)
        print("Correct Answer:", quiz.correct_answer)
        print("Timestamp:", quiz.timestamp)
        print("--" * 20)