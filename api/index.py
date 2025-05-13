from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import sys
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Add the current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# Import the chat module directly
from api.chat import app as chat_app, chat_endpoint

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Mount the chat app
app.post("/api/chat")(chat_endpoint)

# Vercel serverless handler
handler = Mangum(app) 