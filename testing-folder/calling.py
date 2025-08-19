from testing_models import workflow


user_input = input("Enter your question: ")
initial_state = {
"question": user_input
}
result = workflow.invoke(initial_state)
print("Answer:", result["answer"])