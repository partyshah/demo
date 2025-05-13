from enum import Enum
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser

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