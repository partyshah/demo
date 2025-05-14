from typing import TypedDict, List, Dict, Optional, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

class StudentState(TypedDict):
    background: Optional[str]

class TutorState(TypedDict):
    current_phase: str  # "discussion" or "coding"
    current_milestone: str
    student: StudentState
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]
    curriculum: Dict[str, List[str]]
    milestones_completed: List[str]
    milestones_remaining: List[str]
    milestones_identified: List[str]
    current_input: Optional[str]  # Store the current input message