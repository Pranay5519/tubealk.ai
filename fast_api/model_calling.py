
from testing_summary.model_langChain import YouTubeVideoSummarizer
from testing_chatbot.rag.utils_youtube import load_transcript

def generate_summary(url : str)-> str:
    transcripts = load_transcript(url=url)
    summarizer= YouTubeVideoSummarizer()
    response , parsed_output , summary = summarizer.summarize_video(transcripts)
    #formatted_summary = summarizer.format_summary_output(summary=summary)
    return response , parsed_output , summary