from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import sys
import json
from fastapi.responses import JSONResponse

# Create the FastAPI app
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

# Initialize other components when first requested, not at module load
anthropic_client = None
graph = None
compiled_graph = None

def init_dependencies():
    global anthropic_client, graph, compiled_graph
    
    if anthropic_client is None:
        try:
            from anthropic import Anthropic
            anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        except Exception as e:
            print(f"Error initializing Anthropic: {str(e)}")
            return False
    
    if graph is None or compiled_graph is None:
        try:
            # Add the backend folder to path so we can import from src
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
                
            from backend.src.langgraph_module.main import build_graph, initialize_session
            graph = build_graph()
            compiled_graph = graph.compile()
        except Exception as e:
            print(f"Error initializing LangGraph: {str(e)}")
            return False
            
    return True

@app.post("/api/chat")
async def chat_endpoint(chat_request: ChatRequest):
    try:
        # Initialize dependencies on first request
        if not init_dependencies():
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to initialize dependencies"},
            )
            
        # Import the main module
        from backend.src.langgraph_module.main import initialize_session
        
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
        # Log the detailed error
        error_type = type(e).__name__
        error_message = str(e)
        print(f"Error in chat_endpoint: {error_type} - {error_message}")
        
        # Return a fallback message
        return JSONResponse(
            status_code=500,
            content={"error": f"{error_type}: {error_message}"},
        )

# Handler for Vercel serverless function
async def handler(request: Request):
    try:
        # Extract the request body
        body = await request.json()
        # Convert to our model
        chat_request = ChatRequest(**body)
        # Process with our endpoint
        return await chat_endpoint(chat_request)
    except Exception as e:
        # Log the error
        error_type = type(e).__name__
        error_message = str(e)
        print(f"Error in handler: {error_type} - {error_message}")
        
        # Return a fallback response
        return JSONResponse(
            status_code=500, 
            content={"error": f"{error_type}: {error_message}"}
        ) 