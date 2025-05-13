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

def simple_chat_handler(messages, session_id=None):
    """
    A simplified handler for chat requests that doesn't rely on async/await.
    This is easier to call from a simple Lambda handler.
    """
    try:
        # Initialize dependencies
        if not init_dependencies():
            return {"error": "Failed to initialize dependencies"}, 500
            
        # Import session initializer
        try:
            from backend.src.langgraph_module.main import initialize_session
        except ImportError as e:
            print(f"Error importing initialize_session: {str(e)}")
            return {"error": f"Import error: {str(e)}"}, 500
            
        # Get or create session state
        if session_id and session_id in active_sessions:
            state = active_sessions[session_id]
        else:
            state = initialize_session()
            if session_id:
                active_sessions[session_id] = state
        
        # Make sure we have messages
        if not messages or len(messages) == 0:
            return {"error": "No messages provided"}, 400
        
        latest_message = messages[-1]
        
        if latest_message.get("role") != "user":
            return {"error": "Expected the last message to be from the user"}, 400
        
        # Format messages for the graph
        state["messages"] = messages
        state["current_input"] = latest_message.get("content", "")
        
        # Process with the graph
        updated_state = compiled_graph.invoke(state)
        
        # Update session if needed
        if session_id:
            active_sessions[session_id] = updated_state
    
        # Get the latest assistant message
        latest_assistant_message = updated_state["messages"][-1].get("content", "")
        
        return latest_assistant_message, 200
    except Exception as e:
        # Log the detailed error
        error_type = type(e).__name__
        error_message = str(e)
        print(f"Error in chat_handler: {error_type} - {error_message}")
        
        # Return a fallback message
        return {"error": f"{error_type}: {error_message}"}, 500

@app.post("/api/chat")
async def chat_endpoint(chat_request: ChatRequest):
    try:
        # Convert the request to a list of messages
        messages = [{"role": m.role, "content": m.content} for m in chat_request.messages]
        
        # Call the simplified handler
        result, status_code = simple_chat_handler(messages, chat_request.sessionId)
        
        # Return the result
        if status_code != 200:
            return JSONResponse(status_code=status_code, content=result)
        return result
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