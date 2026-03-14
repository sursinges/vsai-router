from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

from router.router import ask


app = FastAPI()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: Optional[List[Message]] = None
    message: Optional[str] = None


def normalize_messages(request: ChatRequest):

    if request.messages:
        return [m.dict() for m in request.messages]

    if request.message:
        return [
            {
                "role": "user",
                "content": request.message
            }
        ]

    return None


@app.post("/chat")
async def chat(
    request: ChatRequest,
    mode: str = Query("auto")
):

    messages = normalize_messages(request)

    if not messages:
        return {"error": "no message"}

    result = await ask(messages, mode)

    if "error" in result:
        return result

    return {
        "model": result["best"]["model"],
        "response": result["best"]["response"]
    }


@app.post("/debug")
async def debug(
    request: ChatRequest,
    mode: str = Query("auto")
):

    messages = normalize_messages(request)

    if not messages:
        return {"error": "no message"}

    return await ask(messages, mode)