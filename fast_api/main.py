from fastapi import FastAPI
from pydantic import BaseModel
from fast_api.model_calling import ModelCalling

# Request body schema
class InputSchema(BaseModel):
    input_url: str

# Create app
app = FastAPI()
modelcalling = ModelCalling()
# POST endpoint
@app.post("/summarize")
def summarizer(data: InputSchema):
    response , parsed_output , summary = modelcalling.generate_summary(url=data.input_url)
    return {
        "summary": summary,
        "parsed_output": parsed_output,
        "model_response": response
        }

@app.post("/quiz")
def quiz(data: InputSchema):
    response = modelcalling.generate_quiz(url=data.input_url)
    return {'response' : response}
    