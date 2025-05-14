import json
from typing import List, Dict, Any, AsyncGenerator
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .utils.messages import ClientMessage, convert_to_anthropic_messages

from .utils.curriculum import create_tictactoe_curriculum
from .utils.state import TutorState
from .utils.graph import build_graph
load_dotenv(".env.local")

app = FastAPI()

class Request(BaseModel):
    messages: List[ClientMessage]


def initialize_session() -> TutorState:
    """Initialize a new tutoring session with the given curriculum."""
    tic_tac_toe_curriculum = create_tictactoe_curriculum()
    
    student = {
        "background": "A high school student who is learning Python for the first time. They have some experience with Java. They have take a introduction course to Computer Science so they understand the basics of programming like loops, conditionals, variables, and data structures.",
    }
    
    # Initial session state
    return {
        'current_phase': "DISCUSSION",
        'current_milestone': None,
        "student": student,
        "messages": [],
        "curriculum": tic_tac_toe_curriculum.model_dump(),  
        "milestones_completed": [],
        "milestones_remaining": [m.id for m in tic_tac_toe_curriculum.milestones], 
        "milestones_identified": [],
        "current_input": None
    }

graph = build_graph()
state = initialize_session()

async def stream_text(messages: List[Dict[str, Any]], protocol: str = 'data') -> AsyncGenerator[str, None]:
    """Stream text from Claude via LangGraph."""
    
    state["messages"] = messages[:-1]
    state["current_input"] = messages[-1]
    async for chunk in graph.astream(
        state,
        stream_mode="custom", 
    ):
        if "response_chunk" in chunk:
            yield f'0:{json.dumps(chunk["response_chunk"])}\n'
    
    yield 'e:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0},"isContinued":false}\n'


@app.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query('data')):
    """Handle chat requests and stream responses."""
    messages = request.messages
    anthropic_messages = convert_to_anthropic_messages(messages)
    
    response = StreamingResponse(stream_text(anthropic_messages, protocol))
    response.headers['x-vercel-ai-data-stream'] = 'v1'
    return response