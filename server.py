from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from agent import agent_answer
from fastapi.responses import StreamingResponse

import os
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.getenv("HOST_URL")

app = FastAPI(
    title="English Exam RAG Agent",
    description="FAISS-based RAG agent for Taiwan school exams",
    version="0.1.0",
)

origins = [
    "http://localhost:8000",  # 如果 mac 本地開發頁面
    "http://mac_ip:port",  # 你的 mac 前端頁面
    "*",  # 測試用，允許所有來源
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------
# Request / Response Schema
# ---------

class PromptRequest(BaseModel):
    prompt: str

class AnswerResponse(BaseModel):
    answer: str

# 將 static 資料夾掛載到 /static，因爲 fastapi 內部有自己的 directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

# ---------
# Health Check
# ---------

@app.get("/health")
def health_check():
    return {"status": "ok"}

# ---------
# 處理 user query 並 stream output
# ---------

@app.post("/ask", response_model=AnswerResponse)
def ask_question_stream(req: PromptRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    return StreamingResponse(agent_answer(req.prompt), media_type="text/event-stream")
