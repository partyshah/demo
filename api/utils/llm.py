from langchain_anthropic import ChatAnthropic
from ..settings import ANTHROPIC_API_KEY

llm = ChatAnthropic(
    model="claude-3-5-sonnet-20240620",
    temperature=0,
    max_tokens=1024,
    timeout=None,
    max_retries=2,
    api_key=ANTHROPIC_API_KEY,
    streaming=True,
)