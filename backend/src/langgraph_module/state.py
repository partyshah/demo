from typing import TypedDict, List, Dict, Optional

class StudentState(TypedDict):
    background: Optional[str]

class TutoringSessionState(TypedDict):
    phase: str  # "discussion" or "coding"
    student: StudentState
    messages: List[Dict[str, str]]
    curriculum: Dict[str, List[str]]
    curriculum_completed: List[str]
    curriculum_remaining: List[str]
    curriculum_identified: List[str]
    current_input: Optional[str]  # Store the current input message