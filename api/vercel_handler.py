from index import app
import json

def handler(request):
    """Simple handler function for Vercel"""
    try:
        # Basic routing
        path = request.get('path', '/')
        method = request.get('method', 'GET')
        
        if path == '/api/health' and method == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok'}),
                'headers': {'Content-Type': 'application/json'}
            }
            
        if path == '/api/chat' and method == 'POST':
            body = request.get('body', '{}')
            if isinstance(body, str):
                body = json.loads(body)
                
            # Import the chat module
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Process the request
            from api.chat import ChatRequest, chat_endpoint
            chat_request = ChatRequest(**body)
            result = chat_endpoint(chat_request)
            
            return {
                'statusCode': 200,
                'body': json.dumps(result),
                'headers': {'Content-Type': 'application/json'}
            }
            
        # Default 404
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Not Found'}),
            'headers': {'Content-Type': 'application/json'}
        }
    except Exception as e:
        # Log the error
        print(f"Error: {str(e)}")
        
        # Return a 500 error
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': str(type(e))
            }),
            'headers': {'Content-Type': 'application/json'}
        } 