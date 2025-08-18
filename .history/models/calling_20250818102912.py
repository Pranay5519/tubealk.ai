from models.testing_models import workflow

if __name__ == "__main__":
    initial_state = {
        "question": "what is the capital of France?"
    }
    result = workflow.invoke(initial_state)
    print("Answer:", result["answer"])