from langgraph.graph import StateGraph, END
from src.langgraph_module.state import TutoringSessionState
from src.langgraph_module.node import process_student_message, router, phase_transition, continue_current_phase, generate_tutor_message
from src.langgraph_module.curriculum import create_tictactoe_curriculum

# Initialize the graph
def build_graph():
    workflow = StateGraph(TutoringSessionState)
    
    # Add nodes
    workflow.add_node("process_student_message", process_student_message)
    workflow.add_node("phase_transition", phase_transition)
    workflow.add_node("continue_current_phase", continue_current_phase)
    workflow.add_node("generate_tutor_message", generate_tutor_message)
    
    # Add edges
    workflow.add_conditional_edges(
        "process_student_message",
        router
    )
    workflow.add_edge("phase_transition", "generate_tutor_message")
    workflow.add_edge("continue_current_phase", "generate_tutor_message")
    workflow.add_edge("generate_tutor_message", END)
    
    # Set entrypoint
    workflow.set_entry_point("process_student_message")
    
    return workflow

def initialize_session() -> TutoringSessionState:
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

def run_tutoring_session():
    workflow = build_graph()
    compiled_graph = workflow.compile()
    
    state = initialize_session()
    
    print("Tutoring Session Started (type 'exit' to quit)")
    
    from pprint import pprint
    while True:
        # Get user input
        user_input = input("\nStudent: ")
        if user_input.lower() == 'exit':
            break
        
        state["current_input"] = user_input
        
        # Run the graph
        state = compiled_graph.invoke(state)
        
        # Display the response
        last_message = state["messages"][-1]["content"]
        print(f"\nTutor: {last_message}")

        # Show current state information
        print(f"\n[DEBUG]\nCurrent Phase: {state['current_phase']}")
        if state['milestones_remaining']:
            pprint(f"Milestones remaining: {state['milestones_remaining']}")
        print(f"Completed: {state['milestones_completed']}")

if __name__ == "__main__":
    run_tutoring_session()