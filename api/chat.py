from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from anthropic import Anthropic
import sys

# Add the backend folder to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.src.langgraph_module.main import build_graph, initialize_session

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    sessionId: str = None

# Store active sessions
active_sessions: Dict[str, Any] = {}

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Build the LangGraph workflow
graph = build_graph()
compiled_graph = graph.compile()

@app.post("/api/chat")
async def chat_endpoint(chat_request: ChatRequest):
    try:
        if chat_request.sessionId and chat_request.sessionId in active_sessions:
            state = active_sessions[chat_request.sessionId]
        else:
            state = initialize_session()
            if chat_request.sessionId:
                active_sessions[chat_request.sessionId] = state
        
        latest_message = chat_request.messages[-1]
        
        if latest_message.role != "user":
            return {"role": "assistant", "content": "Expected the last message to be from the user."}
        
        state["messages"] = [{"role": m.role, "content": m.content} for m in chat_request.messages]
        
        state["current_input"] = latest_message.content
        
        updated_state = compiled_graph.invoke(state)
        
        if chat_request.sessionId:
            active_sessions[chat_request.sessionId] = updated_state
    
        latest_assistant_message = updated_state["messages"][-1]["content"]
        
        return latest_assistant_message
    except Exception as e:
        # Fallback to direct Anthropic API if LangGraph fails
        messages = [
            {"role": m.role, "content": m.content} for m in chat_request.messages
        ]
        return {"error": str(e)}

# Handler for Vercel serverless function
async def handler(request: Request):
    # Extract the request body
    body = await request.json()
    # Convert to our model
    chat_request = ChatRequest(**body)
    # Process with our endpoint
    return await chat_endpoint(chat_request) 