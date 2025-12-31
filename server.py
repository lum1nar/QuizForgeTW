from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import agent_answer

app = FastAPI(
    title="English Exam RAG Agent",
    description="FAISS-based RAG agent for Taiwan school exams",
    version="0.1.0",
)

# ---------
# Request / Response Schema
# ---------

class PromptRequest(BaseModel):
    prompt: str

class AnswerResponse(BaseModel):
    answer: str

# ---------
# Health Check
# ---------

@app.get("/health")
def health_check():
    return {"status": "ok"}

# ---------
# Main API
# ---------

@app.post("/ask", response_model=AnswerResponse)
def ask_question(req: PromptRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        answer = agent_answer(req.prompt)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
