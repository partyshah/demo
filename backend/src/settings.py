import os
from dotenv import load_dotenv
load_dotenv()

if "ANTHROPIC_API_KEY" not in os.environ:
    raise ValueError("ANTHROPIC_API_KEY is not set")

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]