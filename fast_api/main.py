from fastapi import FastAPI
from pydantic import BaseModel
from fast_api.model_calling import generate_summary

# Request body schema
class InputSchema(BaseModel):
    input_url: str

# Create app
app = FastAPI()

# POST endpoint
@app.post("/summarize")
def summarizer(data: InputSchema):
    response , parsed_output , summary = generate_summary(url=data.input_url)
    return {
        "summary": summary,
        "parsed_output": parsed_output,
        "model_response": response
        }
