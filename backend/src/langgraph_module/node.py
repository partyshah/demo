from src.langgraph_module.state import TutoringSessionState
from src.langgraph_module.prompt import discussion_prompt, router_prompt, coding_prompt, extraction_prompt
from src.langgraph_module.llm import llm
from src.langgraph_module.output_parser import router_parser, extraction_parser

def process_student_message(state: TutoringSessionState) -> TutoringSessionState:
    """Process incoming student message and update state."""
    message = state["current_input"]
    
    chain = extraction_prompt | llm | extraction_parser
    response = chain.invoke(
        {
            "curriculum": state["curriculum"],
            "input": state["messages"][-5:] + [{"role": "user", "content": message}],
            "format_instructions": extraction_parser.get_format_instructions(),
        }
    )
    print(f"LLM API CALL: {response=}")
    
    return {
        **state,
        "messages": state["messages"] + [{"role": "user", "content": message}],
        "milestones_identified": response['milestones_identified'],
        "current_milestone": response['current_milestone'],
    }

def router(state: TutoringSessionState) -> str:
    """Decide whether to continue current phase or transition to a new one."""
    chain = router_prompt | llm | router_parser
    response = chain.invoke(
        {
            "curriculum": state["curriculum"],
            "current_milestone": state["milestones_remaining"] if state["milestones_remaining"] else "None",
            'current_phase': state['current_phase'],
            "input": state["messages"],
            "format_instructions": router_parser.get_format_instructions(),
        }
    )
    print(f"LLM API CALL: {response=}")
        
    if state['current_phase'] != response.phase:
        return "phase_transition"
    else:
        return "continue_current_phase"

def phase_transition(state: TutoringSessionState) -> TutoringSessionState:
    """Handle transition to a new teaching phase."""
    print(f"LLM API CALL: Transitioning from {state['current_phase']} phase")
    
    new_state = state.copy()
    
    if state['current_phase'] == "DISCUSSION":
        new_state['current_phase'] = "CODING"
    elif state['current_phase'] == "CODING":
        new_state['current_phase'] = "DISCUSSION"
    else:
        raise ValueError(f"Invalid phase: {state['current_phase']}")
    
    return new_state

def continue_current_phase(state: TutoringSessionState) -> TutoringSessionState:
    """Continue with the current teaching phase."""
    print(f"LLM API CALL: Continuing {state['current_phase']} phase")
    return state

def generate_tutor_message(state: TutoringSessionState) -> TutoringSessionState:
    """Generate a response based on the current teaching phase."""
    phase = state['current_phase']
    current_milestone = state["current_milestone"]

    chain = None
    if phase == "DISCUSSION":
        chain = discussion_prompt | llm
        params = {
            "student_background": state["student"]["background"],
            "curriculum": state["curriculum"],
            "current_milestone": current_milestone,
            "completed_milestones": state["milestones_completed"],
            "remaining_milestones": state["milestones_remaining"],
            "identified_milestones": state["milestones_identified"],
            "input": state["messages"][-5:] + [state["current_input"]],
        }
    elif phase == "CODING":
        chain = coding_prompt | llm
        params = {
            "curriculum": state["curriculum"],
            "current_milestone": current_milestone,
            "input": state["messages"][-5:] + [state["current_input"]],
        }
    else:
        raise ValueError(f"Invalid phase: {phase}")
    
    response = chain.invoke(params)
    state["messages"].append({"role": "tutor", "content": response})
    
    return state