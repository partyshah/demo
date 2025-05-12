from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

@app.post("/api/chat")
async def chat_endpoint(chat_request: ChatRequest):
    # Prepare messages for Anthropic API
    messages = [
        {"role": m.role, "content": m.content} for m in chat_request.messages
    ]
    try:
        response = anthropic_client.messages.create(
            model="claude-3-7-sonnet-latest",
            messages=messages,
            max_tokens=512,
        )
        content = "".join([block.text for block in response.content])
        return {"role": "assistant", "content": content}
    except Exception as e:
        return {"role": "assistant", "content": f"Error: {str(e)}"}
