import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load .env
load_dotenv()

# LangChain expects `OPENAI_API_KEY`, but we’re using OpenRouter
# so we’ll override base_url + api_key manually
llm = ChatOpenAI(
    model="openai/gpt-5-mini",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",  # 👈 Important
    temperature=0.7,
    max_tokens=300,
)

# Run a simple chat
resp = llm.invoke([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing in simple terms."}
])

print(resp.content)
