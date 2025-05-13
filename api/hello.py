from http.server import BaseHTTPRequestHandler
import json
import os
import sys

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {"status": "ok"}
        if self.path == "/api/health":
            response = {"status": "ok", "message": "Health check passed"}
        elif self.path == "/api/debug":
            # Add debug information
            response = {
                "status": "ok",
                "debug": {
                    "path": self.path,
                    "python_version": sys.version,
                    "cwd": os.getcwd(),
                    "dir_contents": os.listdir(os.getcwd()),
                    "env_vars": list(os.environ.keys())
                }
            }
        else:
            response = {
                "status": "ok", 
                "message": "Hello from Vercel Python API",
                "path": self.path
            }
            
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_json = json.loads(post_data.decode())
            
            try:
                # Import the chat module
                parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if parent_dir not in sys.path:
                    sys.path.append(parent_dir)
                    
                from api.chat import simple_chat_handler
                
                # Process the messages
                messages = []
                if "messages" in request_json:
                    for msg in request_json["messages"]:
                        messages.append({
                            "role": msg.get("role", ""),
                            "content": msg.get("content", "")
                        })
                
                # Call the handler
                result, status_code = simple_chat_handler(
                    messages, 
                    request_json.get("sessionId")
                )
                
                # Send the response
                self.send_response(status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Check if result is already a dict or string
                if isinstance(result, dict):
                    response_json = json.dumps(result)
                else:
                    response_json = json.dumps({"content": result})
                    
                self.wfile.write(response_json.encode())
                return
                
            except Exception as e:
                # Send error response
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {
                    "error": str(e),
                    "type": str(type(e))
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
        else:
            # Unknown POST endpoint
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
            return 