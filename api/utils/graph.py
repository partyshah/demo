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
    all_milestone_ids = [m['id'] for m in state['curriculum']['milestones']]
    completed = set(state.get('milestones_completed', []))
    current_milestone = state.get('current_milestone')

    # Bootstrap: If state has no current milestone, but LLM extraction does, set it
    if (not current_milestone or current_milestone == 'None'):
        llm_milestone = response.get('current_milestone')
        if llm_milestone and llm_milestone != 'None':
            current_milestone = llm_milestone

    # Debug: Print current milestone from state and LLM extraction
    print(f"[DEBUG] State current_milestone: {current_milestone}, LLM current_milestone: {response.get('current_milestone')}, milestone_completed: {response.get('milestone_completed')}")

    # Only use LLM to check if the current milestone is complete
    just_completed = None
    if response.get('milestone_completed', False) and current_milestone and current_milestone != 'None':
        if current_milestone not in completed:
            completed.add(current_milestone)
            just_completed = current_milestone

    # Always update milestones_completed in curriculum order
    milestones_completed = [m for m in all_milestone_ids if m in completed]
    # Always update remaining milestones
    remaining = [m for m in all_milestone_ids if m not in completed]

    # Find the next milestone to work on (in curriculum order)
    next_milestone = None
    for milestone_id in remaining:
        milestone = next(m for m in state['curriculum']['milestones'] if m['id'] == milestone_id)
        if all(prereq in completed for prereq in milestone['prerequisites']):
            next_milestone = milestone_id
            break

    # Guard: Never regress to a completed milestone
    if next_milestone in completed:
        next_milestone = None

    # If all milestones are completed
    if response.get('milestone_completed', False) and not next_milestone:
        print("[DEBUG] All milestones completed. No further prompts.")
        new_state = {
            **state,
            "messages": state["messages"] + [{"role": "user", "content": message}],
            "milestones_identified": response['milestones_identified'],
            "current_milestone": None,
            "milestone_feedback": response.get('milestone_feedback', ""),
            "just_completed_milestone": just_completed,
            "milestones_completed": milestones_completed,
            "milestones_remaining": [],
            "current_phase": 'DISCUSSION',
        }
        return new_state

    new_state = {
        **state,
        "messages": state["messages"] + [{"role": "user", "content": message}],
        "milestones_identified": response['milestones_identified'],
        "current_milestone": next_milestone if just_completed else current_milestone,
        "milestone_feedback": response.get('milestone_feedback', ""),
        "just_completed_milestone": just_completed,
        "milestones_completed": milestones_completed,
        "milestones_remaining": remaining,
    }
    # Always reset phase to DISCUSSION for new milestone
    if just_completed and next_milestone:
        print(f"[DEBUG] Advancing to next milestone: {next_milestone}, resetting phase to DISCUSSION.")
        new_state['current_phase'] = 'DISCUSSION'

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
            "current_milestone": state["current_milestone"] if state["current_milestone"] else "None",
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
            "student_background": state["student"].get("background", ""),
            "curriculum": state["curriculum"],
            "current_milestone": current_milestone,
            "completed_milestones": state.get("milestones_completed", []),
            "remaining_milestones": state.get("milestones_remaining", []),
            "identified_milestones": state.get("milestones_identified", []),
            "milestone_feedback": state.get("milestone_feedback", ""),
            "current_phase": state.get("current_phase", ""),
            "just_completed_milestone": state.get("just_completed_milestone", None),
            "history": state.get("messages", [])[-5:],
            "input": state["current_input"],
        }
    elif phase == "CODING":
        prompt = coding_prompt
        params = {
            "curriculum": state["curriculum"],
            "current_milestone": current_milestone,
            "completed_milestones": state.get("milestones_completed", []),
            "remaining_milestones": state.get("milestones_remaining", []),
            "identified_milestones": state.get("milestones_identified", []),
            "milestone_feedback": state.get("milestone_feedback", ""),
            "current_phase": state.get("current_phase", ""),
            "just_completed_milestone": state.get("just_completed_milestone", None),
            "history": state.get("messages", [])[-5:],
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
    # Show milestone feedback if present and milestone is not completed
    if state.get('milestone_feedback') and state.get('current_milestone') and state.get('current_milestone') not in state.get('milestones_completed', []):
        response_content = (
            f"⚠️ Feedback on your last submission:\n{state['milestone_feedback']}\n\n" + response_content
        )
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