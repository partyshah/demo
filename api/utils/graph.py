from langgraph.config import get_stream_writer 
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from typing import Dict, Any

from .state import TutorState
from .llm import llm
from .output_parser import extraction_parser
from .prompt import (
    extraction_prompt, 
    discussion_prompt, 
    coding_prompt,
    router_prompt
)
from .output_parser import (
    router_parser,
    extraction_parser,
)

# Graph Nodes
async def process_student_message(state: TutorState) -> TutorState:
    """Extract information from student message to update state and handle milestone progression."""
    writer = get_stream_writer() # TODO: remove this
    writer({"status": "Processing student message..."})
    
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

    # --- Milestone progression logic ---
    # Get all milestone IDs from the curriculum
    all_milestone_ids = [m['id'] for m in state['curriculum']['milestones']]

    completed = set(state.get('milestones_completed', []))
    # If the LLM says the current milestone is completed, add it
    if response.get('milestone_completed', False):
        current = response['current_milestone']
        if current and current != 'None':
            completed.add(current)
            print(f"[DEBUG] Milestone completed: {current}")

    # Always update remaining milestones
    remaining = [m for m in all_milestone_ids if m not in completed]

    # Find the next milestone to work on (in curriculum order)
    next_milestone = remaining[0] if remaining else None

    # Guard: If current milestone is already completed, skip redundant prompt
    if response.get('milestone_completed', False) and not next_milestone:
        print("[DEBUG] All milestones completed. No further prompts.")
        new_state = {
            **state,
            "messages": state["messages"] + [{"role": "user", "content": message}],
            "milestones_identified": response['milestones_identified'],
            "current_milestone": None,
            "milestone_feedback": response.get('milestone_feedback', ""),
            "just_completed_milestone": None,
            "milestones_completed": list(completed),
            "milestones_remaining": [],
            "current_phase": 'DISCUSSION',
        }
        return new_state

    new_state = {
        **state,
        "messages": state["messages"] + [{"role": "user", "content": message}],
        "milestones_identified": response['milestones_identified'],
        "current_milestone": next_milestone,
        # Optionally, you can store feedback for tutor use
        "milestone_feedback": response.get('milestone_feedback', ""),
        "just_completed_milestone": None
    }

    # Only progress if milestone is completed and there are remaining milestones
    if response.get('milestone_completed', False):
        new_state['milestones_completed'] = list(completed)
        new_state['milestones_remaining'] = remaining
        new_state['current_milestone'] = next_milestone
        # Always reset phase to DISCUSSION for new milestone
        if next_milestone:
            print(f"[DEBUG] Advancing to next milestone: {next_milestone}, resetting phase to DISCUSSION.")
            new_state['current_phase'] = 'DISCUSSION'
        # Track just completed milestone for validation feedback
        new_state['just_completed_milestone'] = next_milestone
    else:
        new_state['just_completed_milestone'] = None

    print(f"[DEBUG] State after processing: milestone={new_state['current_milestone']}, phase={new_state.get('current_phase')}, completed={new_state.get('milestones_completed')}")
    return new_state

async def router(state: TutorState) -> Dict[str, Any]:
    """Determine whether to continue current phase or transition."""
    writer = get_stream_writer()
    writer({"status": "Determining teaching phase..."})
    
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

async def phase_transition(state: TutorState) -> TutorState:
    """Handle transition to a new teaching phase."""
    writer = get_stream_writer()
    writer({"status": f"Transitioning to {state['current_phase']} phase..."})
    
    new_state = state.copy()
    
    if state['current_phase'] == "DISCUSSION":
        new_state['current_phase'] = "CODING"
    elif state['current_phase'] == "CODING":
        new_state['current_phase'] = "DISCUSSION"
    else:
        raise ValueError(f"Invalid phase: {state['current_phase']}")
    
    return new_state

async def continue_current_phase(state: TutorState) -> TutorState:
    """Continue with the current teaching phase."""
    writer = get_stream_writer()
    writer(f"LLM API CALL: Continuing {state['current_phase']} phase")
    return state

async def generate_tutor_message(state: TutorState) -> TutorState:
    """Generate a tutor response based on the current phase, with streaming."""
    writer = get_stream_writer()
    writer({"status": "Generating tutor response..."})

    # Debug log to confirm state before prompt generation
    print(f"[DEBUG] Generating tutor message for milestone={state['current_milestone']}, phase={state['current_phase']}, completed={state.get('milestones_completed')}")
    
    phase = state['current_phase']
    current_milestone = state["current_milestone"]

    prompt = None
    if phase == "DISCUSSION":
        prompt = discussion_prompt
        params = {
            "student_background": state["student"]["background"],
            "curriculum": state["curriculum"],
            "current_milestone": current_milestone,
            "completed_milestones": state["milestones_completed"],
            "remaining_milestones": state["milestones_remaining"],
            "identified_milestones": state["milestones_identified"],
            "input": state["current_input"], #change this to last 5 messages
        }
    elif phase == "CODING":
        prompt = coding_prompt
        params = {
            "curriculum": state["curriculum"],
            "current_milestone": current_milestone,
            "input": state["current_input"],
        }
    else:
        raise ValueError(f"Invalid phase: {phase}")
    
    prompt_messages = prompt.format_messages(**params)
    
    response_content = ""
    async for chunk in llm.astream(prompt_messages):
        if chunk.content:
            response_content += chunk.content
            writer({"response_chunk": chunk.content})

    # Prepend congratulatory message if a milestone was just completed
    new_state = state.copy()
    if state.get('just_completed_milestone'):
        completed_milestone = state['just_completed_milestone']
        validation_message = (
            f"🎉 Great job! You've successfully completed the milestone: {completed_milestone}. "
            "Your code meets the requirements. Let's move on to the next part!\n\n"
        )
        response_content = validation_message + response_content
        new_state['just_completed_milestone'] = None

    new_state["response"] = response_content
    new_state["messages"] = state["messages"] + [AIMessage(content=response_content)]
    
    return new_state


# Graph Construction
def build_graph():
    workflow = StateGraph(TutorState)
    
    workflow.add_node("process_student_message", process_student_message)
    workflow.add_node("phase_transition", phase_transition)
    workflow.add_node("continue_current_phase", continue_current_phase)
    workflow.add_node("generate_tutor_message", generate_tutor_message)
    
    workflow.add_conditional_edges(
        "process_student_message",
        router
    )
    workflow.add_edge("phase_transition", "generate_tutor_message")
    workflow.add_edge("continue_current_phase", "generate_tutor_message")
    workflow.add_edge("generate_tutor_message", END)

    workflow.set_entry_point("process_student_message")
    
    return workflow.compile()