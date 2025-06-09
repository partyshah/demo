from typing import TypedDict, List, Dict, Optional, Any
import uuid

class StudentState(TypedDict):
    background: str

class TutorState(TypedDict):
    session_id: str
    current_milestone: Optional[str]
    student: StudentState
    messages: List[Dict[str, str]]  # Simple dict format instead of LangChain objects
    curriculum: Dict[str, Any]
    milestones_completed: List[str]
    current_input: str

# Session management
sessions: Dict[str, TutorState] = {}

def create_session() -> str:
    """Create a new session and return session_id"""
    session_id = str(uuid.uuid4())
    return session_id

def get_session(session_id: str) -> Optional[TutorState]:
    """Get session state by ID"""
    state = sessions.get(session_id)
    if state:
        print(f"[STATE MGMT] Retrieved session {session_id}: {len(state.get('messages', []))} messages, milestone {state.get('current_milestone')}", flush=True)
    else:
        print(f"[STATE MGMT] Session {session_id} not found", flush=True)
    return state

def update_session(session_id: str, state: TutorState) -> None:
    """Update session state"""
    print(f"[STATE MGMT] Updating session {session_id}: {len(state.get('messages', []))} messages, milestone {state.get('current_milestone')}", flush=True)
    sessions[session_id] = state