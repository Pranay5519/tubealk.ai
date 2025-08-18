from testing_models import workflow
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
user_input = input("Enter your question: ")
initial_state = {
"question": user_input
}
result = workflow.invoke(initial_state)
print("Answer:", result["answer"])