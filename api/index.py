from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import sys
from fastapi.middleware.cors import CORSMiddleware
import json

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
        "dir_contents": os.listdir(os.getcwd()),
        "parent_dir": os.path.dirname(os.getcwd()),
        "parent_dir_contents": os.listdir(os.path.dirname(os.getcwd())) if os.path.dirname(os.getcwd()) else []
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

# For Vercel, we don't use Mangum but implement a direct handler instead
async def handler(event, context):
    """AWS Lambda / Vercel compatible handler"""
    # Create an asgi app
    asgi_app = app
    
    # Convert the Lambda event to a format FastAPI understands
    path = event.get('path', '')
    http_method = event.get('httpMethod', '')
    headers = event.get('headers', {})
    query_string = event.get('queryStringParameters', {})
    body = event.get('body', '')
    
    # Build the ASGI scope
    scope = {
        'type': 'http',
        'path': path,
        'raw_path': path.encode(),
        'method': http_method,
        'query_string': '&'.join([f"{k}={v}" for k, v in query_string.items()]).encode() if query_string else b'',
        'headers': [[k.lower().encode(), v.encode()] for k, v in headers.items()],
        'client': ('0.0.0.0', 0),
        'server': ('vercel', 0),
    }
    
    # Create a simple async generator for the body
    async def receive():
        return {
            'type': 'http.request',
            'body': body.encode() if isinstance(body, str) else body,
            'more_body': False,
        }
    
    # Create a response builder
    response_body = []
    response_status = [200]
    response_headers = [{}]
    
    async def send(message):
        if message['type'] == 'http.response.start':
            response_status[0] = message.get('status', 200)
            response_headers[0] = {k.decode(): v.decode() for k, v in message.get('headers', [])}
        elif message['type'] == 'http.response.body':
            response_body.append(message.get('body', b''))
    
    # Call the ASGI app
    await asgi_app(scope, receive, send)
    
    # Build the response
    response = {
        'statusCode': response_status[0],
        'headers': response_headers[0],
        'body': b''.join(response_body).decode(),
        'isBase64Encoded': False,
    }
    
    return response 