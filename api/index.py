from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import sys
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Add our app paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import chat

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

# Add routes from chat module
app.include_router(chat.app)

# Vercel serverless handler
handler = Mangum(app) 