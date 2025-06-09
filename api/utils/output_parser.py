from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

class TutoringResponse(BaseModel):
    message: str = Field(
        description="The conversational response to the student using Socratic method"
    )
    milestone_completed: str = Field(
        description="The exact milestone ID (m1, m2, m3, m4) that was completed, or 'none' if no milestone was completed"
    )
    feedback: str = Field(
        description="Brief assessment of their progress or what's missing"
    )

tutoring_parser = JsonOutputParser(pydantic_object=TutoringResponse)