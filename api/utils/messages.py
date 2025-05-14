from typing import List, Any, Dict
from pydantic import BaseModel

class ClientMessage(BaseModel):
    role: str
    content: str

def convert_to_anthropic_messages(messages: List[ClientMessage]) -> List[Dict[str, Any]]:
    """Convert client messages to Anthropic's format."""
    anthropic_messages = []

    for message in messages:
        content = message.content
        
        role = message.role
        if role not in ["user", "assistant"]:
            role = "user" # Default unknown roles to user

        anthropic_messages.append({
            "role": role,
            "content": content
        })
        
        
    return anthropic_messages
