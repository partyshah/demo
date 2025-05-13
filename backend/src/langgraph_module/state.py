from typing import TypedDict, List, Dict, Optional

class StudentState(TypedDict):
    background: Optional[str]

class TutoringSessionState(TypedDict):
    current_phase: str  # "discussion" or "coding"
    current_milestone: str
    student: StudentState
    messages: List[Dict[str, str]]
    curriculum: Dict[str, List[str]]
    milestones_completed: List[str]
    milestones_remaining: List[str]
    milestones_identified: List[str]
    current_input: Optional[str]  # Store the current input message