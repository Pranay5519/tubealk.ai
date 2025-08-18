from testing_models import workflow
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
if __name__ == "__main__":
    initial_state = {
        "question": "what is the capital of France?"
    }
    result = workflow.invoke(initial_state)
    print("Answer:", result["answer"])