from src.langgraph_module.state import TutoringSessionState
from src.langgraph_module.prompt import discussion_prompt, router_prompt, coding_prompt
from src.langgraph_module.llm import llm
from src.langgraph_module.output_parser import router_parser

def process_student_message(state: TutoringSessionState) -> TutoringSessionState:
    """Process incoming student message and update state."""
    message = state["current_input"]
    print(f"LLM API CALL: Processing student message: {message}")
    
    # Create a new messages list with the user's message added
    new_messages = state["messages"] + [{"role": "user", "content": message}]
    
    # Return the complete state with the updated messages
    return {**state, "messages": new_messages}

def router(state: TutoringSessionState) -> str:
    """Decide whether to continue current phase or transition to a new one."""
    chain = router_prompt | llm | router_parser
    response = chain.invoke(
        {
            "curriculum": state["curriculum"],
            "current_milestone": state["curriculum_remaining"][0] if state["curriculum_remaining"] else "None",
            "current_phase": state["phase"],
            "input": state["messages"],  # Add message history
            "format_instructions": router_parser.get_format_instructions(),
        }
    )
    print(f"LLM API CALL: Router decision: {response.phase} - Reasoning: {response.reasoning}")
        
    # Check if we need to transition or continue
    if state["phase"] != response.phase:
        return "phase_transition"
    else:
        return "continue_current_phase"

def phase_transition(state: TutoringSessionState) -> TutoringSessionState:
    """Handle transition to a new teaching phase."""
    print(f"LLM API CALL: Transitioning from {state['phase']} phase")
    
    # Create a new state object instead of modifying the existing one
    new_state = state.copy()
    
    if state["phase"] == "DISCUSSION":
        new_state["phase"] = "CODING"
    elif state["phase"] == "CODING":
        new_state["phase"] = "DISCUSSION"
        if new_state["curriculum_remaining"]:
            completed = new_state["curriculum_remaining"].pop(0)
            new_state["curriculum_completed"].append(completed)
    else:
        raise ValueError(f"Invalid phase: {state['phase']}")
    
    return new_state

def continue_current_phase(state: TutoringSessionState) -> TutoringSessionState:
    """Continue with the current teaching phase."""
    print(f"LLM API CALL: Continuing {state['phase']} phase")
    return state

def generate_tutor_message(state: TutoringSessionState) -> TutoringSessionState:
    """Generate a response based on the current teaching phase."""
    phase = state["phase"]
    current_milestone = state["curriculum_remaining"][0] if state["curriculum_remaining"] else "None"

    chain = None
    if phase == "DISCUSSION":
        chain = discussion_prompt | llm
        params = {
            "student_background": state["student"]["background"],
            "curriculum": state["curriculum"],
            "current_milestone": current_milestone,
            "completed_milestones": state["curriculum_completed"],
            "remaining_milestones": state["curriculum_remaining"],
            "identified_milestones": state["curriculum_identified"],
            "input": state["current_input"],
        }
    elif phase == "CODING":
        chain = coding_prompt | llm 
        params = {
            "curriculum": state["curriculum"],
            "current_milestone": current_milestone,
            "input": state["current_input"],
        }
    else:
        raise ValueError(f"Invalid phase: {phase}")
    
    response = chain.invoke(params)
    state["messages"].append({"role": "tutor", "content": response})
    
    return state