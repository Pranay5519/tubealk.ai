from utility_functions import prompt_template

youtube_captions = "THESE ARE YOUTUBE CAPTIONS"
user_input = "THIS IS A USER INPUT"
formatted_prompt = prompt_template.format(
        transcript=youtube_captions,
        question=user_input
    )
print(formatted_prompt)