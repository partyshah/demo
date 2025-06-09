from typing import List, Dict, Any, Optional, AsyncGenerator
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from .utils.messages import ClientMessage, convert_to_anthropic_messages

from .utils.curriculum import create_tictactoe_curriculum
from .utils.state import TutorState, create_session, get_session, update_session, sessions
from .utils.graph import build_graph

load_dotenv(".env.local")

app = FastAPI()

class ChatRequest(BaseModel):
    messages: List[ClientMessage]
    session_id: Optional[str] = None
    sessionId: Optional[str] = None  # Alternative field name

class ChatResponse(BaseModel):
    content: str
    session_id: str

def initialize_session(session_id: str) -> TutorState:
    """Initialize a new tutoring session with the given curriculum."""
    tic_tac_toe_curriculum = create_tictactoe_curriculum()
    
    student = {
        "background": "A high school student who is learning Python for the first time. They have some experience with Java. They have taken an introduction course to Computer Science so they understand the basics of programming like loops, conditionals, variables, and data structures."
    }
    
    return {
        'session_id': session_id,
        'current_milestone': None,
        "student": student,
        "messages": [],
        "curriculum": tic_tac_toe_curriculum.model_dump(),  
        "milestones_completed": [],
        "current_input": ""
    }

graph = build_graph()

@app.post("/api/chat")
async def handle_chat(request: ChatRequest):
    """Handle chat requests with streaming for Vercel AI SDK compatibility."""
    print(f"\n[API] === STREAMING CHAT REQUEST ===", flush=True)
    
    # Try both session_id fields
    session_id = request.session_id or request.sessionId
    print(f"[API] Session ID (session_id): {request.session_id}", flush=True)
    print(f"[API] Session ID (sessionId): {request.sessionId}", flush=True)
    print(f"[API] Final session ID: {session_id}", flush=True)
    print(f"[API] Message count: {len(request.messages)}", flush=True)
    
    response = StreamingResponse(
        stream_chat_response(request.messages, session_id),
        media_type="text/plain"
    )
    response.headers['x-vercel-ai-data-stream'] = 'v1'
    return response

@app.post("/api/chat/json", response_model=ChatResponse)
async def handle_chat_json(request: ChatRequest):
    """Handle chat requests with JSON response (non-streaming)."""
    print(f"\n[API] === JSON CHAT REQUEST ===")
    print(f"[API] Requested session_id: {request.session_id}")
    print(f"[API] Message count: {len(request.messages)}")
    
    try:
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = create_session()
            print(f"[API] Created new session: {session_id}")
        else:
            print(f"[API] Using existing session: {session_id}")
        
        state = get_session(session_id)
        if not state:
            print(f"[API] No existing state found, initializing new session")
            state = initialize_session(session_id)
            update_session(session_id, state)
        else:
            print(f"[API] Retrieved existing state with {len(state.get('messages', []))} messages")
        
        # Convert messages and get current input
        anthropic_messages = convert_to_anthropic_messages(request.messages)
        if not anthropic_messages:
            print(f"[API] ERROR: No messages provided")
            raise HTTPException(status_code=400, detail="No messages provided")
        
        current_input = anthropic_messages[-1]["content"]
        print(f"[API] Current input: {current_input[:100]}{'...' if len(current_input) > 100 else ''}")
        
        # Update state with current input and message history
        state["current_input"] = current_input
        state["messages"] = anthropic_messages[:-1]  # All except current message
        print(f"[API] Updated state with {len(state['messages'])} previous messages")
        
        # Process through graph
        print(f"[API] Invoking LangGraph processing...")
        result = await graph.ainvoke(state)
        
        # Update session state
        update_session(session_id, result)
        print(f"[API] Updated session state")
        
        # Extract response content
        if result["messages"]:
            response_content = result["messages"][-1]["content"]
            print(f"[API] Response content length: {len(response_content)} characters")
        else:
            response_content = "I apologize, but I couldn't generate a response. Please try again."
            print(f"[API] WARNING: No response messages generated, using fallback")
        
        print(f"[API] === CHAT REQUEST COMPLETE ===\n")
        return ChatResponse(content=response_content, session_id=session_id)
        
    except Exception as e:
        print(f"[API] ERROR: Exception in handle_chat: {str(e)}")
        import traceback
        print(f"[API] ERROR: Traceback: {traceback.format_exc()}")
        print(f"[API] === CHAT REQUEST FAILED ===\n")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

async def stream_chat_response(messages: List[ClientMessage], session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """Stream chat response in Vercel AI SDK format."""
    try:
        # Enhanced session detection with fallback
        found_session_id = None
        
        if session_id:
            print(f"[SESSION] Received session ID: {session_id}", flush=True)
            found_session_id = session_id
        else:
            print(f"[SESSION] No session ID provided, using fallback detection...", flush=True)
            
            # FALLBACK 1: If there's only one session, use it (common case)
            if len(sessions) == 1:
                found_session_id = list(sessions.keys())[0]
                print(f"[SESSION] Using single existing session: {found_session_id}", flush=True)
            
            # FALLBACK 2: Look for a session that matches conversation length
            elif len(messages) > 1:
                target_length = len(messages) - 1  # Expected message count in existing session
                for existing_session_id, existing_state in sessions.items():
                    existing_count = len(existing_state.get('messages', []))
                    if existing_count == target_length:
                        # Additional check: compare last message
                        existing_messages = existing_state.get('messages', [])
                        if (existing_messages and len(messages) > 1 and 
                            existing_messages[-1].get('content', '') == messages[-2].content):
                            found_session_id = existing_session_id
                            print(f"[SESSION] Found session by message count and content: {found_session_id}", flush=True)
                            break
        
        # Create new session if none found
        if not found_session_id:
            found_session_id = create_session()
            print(f"[SESSION] Created new session: {found_session_id}", flush=True)
        
        # Get or create state
        state = get_session(found_session_id)
        if not state:
            print(f"[SESSION] Initializing new session: {found_session_id}", flush=True)
            state = initialize_session(found_session_id)
            update_session(found_session_id, state)
        else:
            print(f"[SESSION] Using existing session: {found_session_id} with {len(state.get('messages', []))} messages", flush=True)
        
        # Convert messages and process
        anthropic_messages = convert_to_anthropic_messages(messages)
        if not anthropic_messages:
            yield f'0:{{\"type\":\"error\",\"error\":\"No messages provided\"}}\n'
            return
        
        current_input = anthropic_messages[-1]["content"]
        state["current_input"] = current_input
        state["messages"] = anthropic_messages[:-1]
        
        # Process through graph
        result = await graph.ainvoke(state)
        update_session(found_session_id, result)
        
        # Extract response content
        if result["messages"]:
            response_content = result["messages"][-1]["content"]
        else:
            response_content = "I apologize, but I couldn't generate a response. Please try again."
        
        # Stream the response content word by word
        words = response_content.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f'0:{json.dumps(chunk)}\n'
        
        # Send completion signal
        yield f'e:{{\"finishReason\":\"stop\",\"usage\":{{\"promptTokens\":0,\"completionTokens\":0}},\"isContinued\":false}}\n'
        
    except Exception as e:
        print(f"[STREAMING] ERROR: {str(e)}", flush=True)
        yield f'0:{{\"type\":\"error\",\"error\":\"Error processing request\"}}\n'


@app.post("/api/new-session")
async def create_new_session():
    """Create a new tutoring session."""
    print(f"\n[API] === NEW SESSION REQUEST ===")
    session_id = create_session()
    print(f"[API] Created session: {session_id}")
    
    state = initialize_session(session_id)
    milestone_count = len(state['curriculum']['milestones'])
    print(f"[API] Initialized session with {milestone_count} total milestones")
    
    update_session(session_id, state)
    print(f"[API] Stored session state")
    print(f"[API] === NEW SESSION COMPLETE ===\n")
    
    return {"session_id": session_id}