from langgraph.graph import StateGraph, END

from .state import TutorState
from .llm import llm
from .output_parser import tutoring_parser
from .prompt import unified_tutoring_prompt

def log(message: str) -> None:
    """Log with immediate flush for real-time output"""
    print(message, flush=True)

async def process_message(state: TutorState) -> TutorState:
    """Process student message with simplified Socratic tutoring."""
    session_id = state.get("session_id", "unknown")
    log(f"\n[SESSION {session_id}] === PROCESSING MESSAGE ===")
    log(f"[INPUT] Message: {state['current_input'][:100]}{'...' if len(state['current_input']) > 100 else ''}")
    log(f"[STATE IN] Current milestone: {state.get('current_milestone')}")
    log(f"[STATE IN] Completed milestones: {state.get('milestones_completed', [])}")
    
    try:
        message = state["current_input"]
        updated_messages = state["messages"] + [{"role": "user", "content": message}]
        
        # Strict forward-only milestone management
        all_milestone_ids = [m['id'] for m in state['curriculum']['milestones']]
        completed = set(state.get('milestones_completed', []))
        current_milestone = state.get('current_milestone')
        
        log(f"[MILESTONE GUARD] All milestones: {all_milestone_ids}")
        log(f"[MILESTONE GUARD] Previously completed: {list(completed)}")
        log(f"[MILESTONE GUARD] Current milestone: {current_milestone}")
        
        # GUARD: Ensure completed milestones are never lost or reduced
        if len(completed) > len(state.get('milestones_completed', [])):
            log(f"[MILESTONE GUARD] WARNING: Completed milestones increased unexpectedly")
        
        # GUARD: Find current milestone if none set - use curriculum order ONLY
        if not current_milestone:
            for milestone_id in all_milestone_ids:
                if milestone_id not in completed:
                    current_milestone = milestone_id
                    log(f"[MILESTONE GUARD] Bootstrap to first incomplete: {current_milestone}")
                    break
        
        # GUARD: Prevent working on completed milestones
        if current_milestone and current_milestone in completed:
            log(f"[MILESTONE GUARD] BLOCKING: Attempted to work on completed milestone {current_milestone}")
            # Find next incomplete milestone
            for milestone_id in all_milestone_ids:
                if milestone_id not in completed:
                    current_milestone = milestone_id
                    log(f"[MILESTONE GUARD] Redirected to next incomplete: {current_milestone}")
                    break
        
        # Available milestones (not yet completed, in order)
        available_milestones = [m for m in all_milestone_ids if m not in completed]
        log(f"[MILESTONE GUARD] Available milestones: {available_milestones}")
        
        # PRE-ASSESSMENT: Check if student might be completing the current milestone
        # This helps us determine the correct state to pass to the LLM
        
        # Single LLM call for Socratic tutoring + assessment
        log(f"[LLM CALL] Starting unified tutoring response...")
        chain = unified_tutoring_prompt | llm | tutoring_parser
        response = chain.invoke({
            "student_background": state["student"]["background"],
            "curriculum": state["curriculum"],
            "current_milestone": current_milestone,
            "milestones_completed": list(completed),
            "available_milestones": available_milestones,
            "history": updated_messages[-5:],
            "input": message,
        })
        log(f"[LLM RESPONSE] Response: {response}")
        
        # STRICT milestone completion logic - only allow completion of current milestone
        new_completed = completed.copy()  # Never lose completed milestones
        just_completed = False
        
        # SIMPLE EXPLICIT MILESTONE COMPLETION - no complex parsing needed
        completed_milestone_id = response.get('milestone_completed', 'none')
        log(f"[COMPLETION GUARD] LLM returned milestone_completed: '{completed_milestone_id}'")
        log(f"[COMPLETION GUARD] Current milestone: {current_milestone}")
        log(f"[COMPLETION GUARD] Already completed: {current_milestone in completed if current_milestone else 'N/A'}")
        
        # ONLY allow completion if LLM explicitly returns the current milestone ID
        completion_allowed = (completed_milestone_id == current_milestone and 
                            current_milestone and 
                            current_milestone not in completed and
                            current_milestone in all_milestone_ids)
        
        log(f"[COMPLETION DECISION] Explicit milestone ID match: {completed_milestone_id == current_milestone}")
        log(f"[COMPLETION DECISION] Current milestone exists: {bool(current_milestone)}")
        log(f"[COMPLETION DECISION] Not already completed: {current_milestone not in completed if current_milestone else False}")
        log(f"[COMPLETION DECISION] Valid milestone ID: {current_milestone in all_milestone_ids if current_milestone else False}")
        log(f"[COMPLETION DECISION] Final allowed: {completion_allowed}")
        
        if completion_allowed:
            new_completed.add(current_milestone)
            just_completed = True
            log(f"[COMPLETION GUARD] ✅ APPROVED completion of: {current_milestone}")
        else:
            reasons = []
            if completed_milestone_id == 'none':
                reasons.append("LLM returned 'none' - no completion")
            elif completed_milestone_id != current_milestone:
                reasons.append(f"LLM returned '{completed_milestone_id}' but current is '{current_milestone}'")
            if not current_milestone:
                reasons.append("no current milestone set")
            if current_milestone and current_milestone in completed:
                reasons.append("milestone already completed")
            if current_milestone and current_milestone not in all_milestone_ids:
                reasons.append("invalid milestone ID")
            
            reason = ", ".join(reasons) if reasons else "unknown reason"
            log(f"[COMPLETION GUARD] ❌ REJECTED completion ({reason})")
        
        # STRICT forward progression - only advance if milestone was just completed
        next_milestone = current_milestone  # Default: stay on current
        
        if just_completed:
            log(f"[PROGRESSION GUARD] Finding next milestone after completing {current_milestone}")
            current_index = all_milestone_ids.index(current_milestone)
            
            # Look for next milestone in strict curriculum order
            for i in range(current_index + 1, len(all_milestone_ids)):
                next_id = all_milestone_ids[i]
                if next_id not in new_completed:
                    next_milestone = next_id
                    log(f"[PROGRESSION GUARD] ✅ Advancing to next milestone: {next_milestone}")
                    break
            else:
                # All milestones completed
                next_milestone = None
                log(f"[PROGRESSION GUARD] 🎉 ALL MILESTONES COMPLETED!")
        else:
            log(f"[PROGRESSION GUARD] Staying on current milestone: {current_milestone}")
        
        # GUARD: Final validation - never go backwards
        if next_milestone and next_milestone in new_completed:
            log(f"[PROGRESSION GUARD] BLOCKING: Attempted backwards movement to {next_milestone}")
            next_milestone = current_milestone
        
        # SPECIAL HANDLING: If all milestones are complete, generate celebration response
        if next_milestone is None and len(new_completed) == len(all_milestone_ids):
            log(f"[FINAL MILESTONE] All milestones completed! Generating celebration response...")
            celebration_response = "🎉🎉🎉 CONGRATULATIONS! 🎉🎉🎉\n\nYou have successfully completed ALL milestones for the Tic-Tac-Toe project! You've built:\n\n✅ Board Implementation\n✅ Player Input\n✅ Win Condition Implementation\n✅ Game Loop\n\nYour tic-tac-toe game is now complete and fully functional! You should be proud of your accomplishment. You've demonstrated strong programming skills and problem-solving abilities throughout this project.\n\nFeel free to enhance your game further by adding features like:\n- Better user interface\n- Computer AI opponent\n- Score tracking\n- Different board sizes\n\nGreat job! 🎉"
            
            # Build final state for completed project
            final_state = {
                **state,
                "messages": updated_messages + [{"role": "assistant", "content": celebration_response}],
                "current_milestone": None,  # No more milestones
                "milestones_completed": sorted(list(new_completed), key=lambda x: all_milestone_ids.index(x)),
            }
            
            log(f"[FINAL MILESTONE] Project complete! All {len(new_completed)} milestones done.")
            log(f"[SESSION {session_id}] === PROJECT COMPLETED ===\n")
            
            return final_state
        
        # Build response with congratulations if milestone was just completed
        response_content = response['message']
        if just_completed:
            congratulations = f"🎉 Great job! You've completed milestone: {current_milestone}!\n\n"
            response_content = congratulations + response_content
            log(f"[MESSAGE] Added congratulations for {current_milestone}")
        
        # Final state with protected milestone values
        final_milestones_completed = sorted(list(new_completed), key=lambda x: all_milestone_ids.index(x))
        final_state = {
            **state,
            "messages": updated_messages + [{"role": "assistant", "content": response_content}],
            "current_milestone": next_milestone,
            "milestones_completed": final_milestones_completed,
        }
        
        # FINAL GUARD: Log state transition for verification
        log(f"[STATE GUARD] BEFORE: milestone={state.get('current_milestone')}, completed={state.get('milestones_completed', [])}")
        log(f"[STATE GUARD] AFTER:  milestone={final_state['current_milestone']}, completed={final_state['milestones_completed']}")
        
        # FINAL GUARD: Verify no backwards movement
        if len(final_state['milestones_completed']) < len(state.get('milestones_completed', [])):
            log(f"[STATE GUARD] 🚨 CRITICAL ERROR: Completed milestones decreased!")
            # Restore previous completed milestones
            final_state['milestones_completed'] = state.get('milestones_completed', [])
        
        if (final_state['current_milestone'] and 
            final_state['current_milestone'] in final_state['milestones_completed']):
            log(f"[STATE GUARD] 🚨 CRITICAL ERROR: Current milestone is completed!")
            # Find next incomplete milestone
            for milestone_id in all_milestone_ids:
                if milestone_id not in final_state['milestones_completed']:
                    final_state['current_milestone'] = milestone_id
                    log(f"[STATE GUARD] EMERGENCY CORRECTION: Set to {milestone_id}")
                    break
        
        log(f"[STATE OUT] Current milestone: {final_state['current_milestone']}")
        log(f"[STATE OUT] Completed milestones: {final_state['milestones_completed']}")
        log(f"[SESSION {session_id}] === PROCESSING COMPLETE ===\n")
        
        return final_state
        
    except Exception as e:
        log(f"[ERROR] Exception: {str(e)}")
        import traceback
        log(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        error_message = "I apologize, but I encountered an error. Please try again."
        return {
            **state,
            "messages": state["messages"] + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": error_message}
            ]
        }


# Graph Construction
def build_graph():
    """Build simplified LangGraph with single processing node."""
    workflow = StateGraph(TutorState)
    
    workflow.add_node("process_message", process_message)
    workflow.add_edge("process_message", END)
    workflow.set_entry_point("process_message")
    
    return workflow.compile()