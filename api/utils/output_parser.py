from enum import Enum
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser

class TutoringPhase(str, Enum):
    DISCUSSION = "DISCUSSION"
    CODING = "CODING"

class RouterOutput(BaseModel):
    phase: TutoringPhase = Field(
        description="The phase to transition to or continue with: DISCUSSION or CODING"
    )
    reasoning: str = Field(
        description="Reasoning for why this phase is appropriate given the current context"
    )

router_parser = PydanticOutputParser(pydantic_object=RouterOutput)


class ExtractionOutput(BaseModel):
    milestones_identified: list[str] = Field(
        description="The milestones that the student has identified. Use the curriculum to determine the milestones that the student has identified. Output should be in a list of strings like ['m1', 'm2', 'm3']. If the student has not identified any milestones or this is not being discussed, return an empty list."
    )
    current_milestone: str = Field(
        description="The current milestone that the student is working on. Use the curriculum to determine the current milestone. The student will say what milestone or component they want to work on next. Return one string such as 'm1' or 'm2' or 'm3' or 'm4' etc based on the curriculum. If the student has not started working on a milestone or this is not being discussed, return 'None'."
    )
    milestone_completed: bool = Field(
        description="Whether the student has completed the current milestone. The LLM should analyze the user's code and output and determine if the current milestone is complete."
    )
    milestone_feedback: str = Field(
        description="If the milestone is not completed, provide feedback on what is missing or incorrect. If completed, this can be an empty string."
    )
extraction_parser = JsonOutputParser(pydantic_object=ExtractionOutput)