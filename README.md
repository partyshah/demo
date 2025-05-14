# Next.js + FastAPI Vercel App

A modern web application with a Next.js frontend and FastAPI backend, ready for Vercel deployment. This application demonstrates streaming chat completions using the [Data Stream Protocol](https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol#data-stream-protocol) and the [useChat](https://sdk.vercel.ai/docs/ai-sdk-ui/chatbot#chatbot) hook.

## Tech Stack

- **Frontend**: Next.js 13, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python)
- **AI Integration**: AI SDK, LangChain, LangGraph
- **Deployment**: Vercel

## Features

- Real-time streaming of AI responses
- Modern UI with Tailwind CSS
- Type-safe API calls with TypeScript
- Serverless deployment on Vercel

## Local Development

### Prerequisites

- Node.js 16+ and npm/pnpm
- Python 3.11+
- API keys from your AI provider(s) (e.g., OpenAI, Anthropic)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Set up Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env.local  # Create .env file based on example
   # Edit .env with your API keys
   ```

5. Start the development server:
   ```bash
   npm run dev
   ```

The application will be available at http://localhost:3000.


## Environment Variables

Create a `.env.local` file in the root directory with the following variables:

```
# AI Provider API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key

# Add any other required API keys or configuration
```

## Project Structure

- `/app` - Next.js frontend
- `/api` - FastAPI backend
- `/components` - Reusable UI components
- `/lib` - Shared utilities and types
- `/public` - Static assets
