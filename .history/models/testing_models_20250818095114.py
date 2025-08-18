from langgraph.graph import StateGraph , START  , END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict
from dotenv  import load_dotenv

load_dotenv()


model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Create State

class LLMState(TypedDict):
    question : str
    answer : str
    
# Define the state graph
graph = StateGraph(LLMState)
graph.add_node('qna' ,qna)

graph.add_edge(START, 'qna')
graph.add_edge('qna', END)

workflow = graph.compile()

initial_state = {'question' : 'what is the capital of France?'}
result = workflow.run(initial_state)
print(result)