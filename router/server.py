from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from router.router import ask

app = FastAPI()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: Optional[str] = None
    messages: Optional[List[Message]] = None


@app.post("/chat")
async def chat(request: ChatRequest):

    if request.message:
        messages = [{"role": "user", "content": request.message}]

    elif request.messages:
        messages = [
            {"role": m.role, "content": m.content}
            for m in request.messages
        ]

    else:
        return {"error": "no message"}

    result = await ask(messages)

    if "error" in result:
        return result

    return {
        "model": result["best"]["model"],
        "response": result["best"]["response"]
    }