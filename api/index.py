from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import sys
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

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

@app.get("/api/debug")
async def debug_info():
    """Endpoint to help debug issues with the deployment"""
    debug_info = {
        "python_version": sys.version,
        "sys_path": sys.path,
        "env_vars": {k: "***" if k.lower().endswith("key") else v 
                     for k, v in os.environ.items()},
        "cwd": os.getcwd(),
        "dir_contents": os.listdir(os.getcwd())
    }
    return debug_info

@app.post("/api/chat")
async def api_chat_handler(request: Request):
    # Get the request body
    try:
        body = await request.json()
        
        # Import the chat handler here to avoid circular imports
        import os
        import sys
        
        # Add the parent directory to the path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(parent_dir)
        
        # Now we can import our handler
        try:
            from api.chat import handler as chat_handler
            # Call the handler function
            return await chat_handler(request)
        except ImportError as ie:
            return JSONResponse(
                status_code=500,
                content={"error": f"Import error: {str(ie)}", "sys_path": sys.path},
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": str(type(e))},
        )

# Vercel serverless handler
handler = Mangum(app) 