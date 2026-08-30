from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.llm import chat

app = FastAPI(
    title="AI Agent Course",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str


@app.post("/api/chat", response_model=ChatResponse)
def chat_api(request: ChatRequest):

    answer = chat(request.session_id, request.message)

    return JSONResponse(
        content={"answer": answer},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
