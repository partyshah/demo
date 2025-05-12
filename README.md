# Claude Chatbot (React + FastAPI)

A customizable chatbot application using Anthropic's Claude API, with a React frontend and Python FastAPI backend.

---

## Project Structure

- `src/` — React frontend (Create React App)
- `api/` — Python FastAPI backend

---

## Local Development

### 1. Frontend (React)

```bash
cd /path/to/your/project
npm install
npm start
```
- Runs at [http://localhost:3000](http://localhost:3000)

### 2. Backend (FastAPI)

```bash
cd /path/to/your/project
python3 -m venv venv
source venv/bin/activate
pip install -r api/requirements.txt
```

Create a file `api/.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-...your-key-here...
```

Start the backend:
```bash
uvicorn api.chat:app --reload
```
- Runs at [http://localhost:8000](http://localhost:8000)

---

## Deployment (Vercel Example)

### 1. Deploy Frontend
- Push your code to GitHub.
- Import your repo in [Vercel](https://vercel.com/).
- Set the root directory to your project root (not `src/`).
- Vercel will auto-detect and deploy the React app.

### 2. Deploy Backend
- In Vercel, add a new Python serverless function for your FastAPI backend (see Vercel docs for Python API setup).
- Set the `ANTHROPIC_API_KEY` as an environment variable in Vercel's dashboard.
- Make sure your API endpoints are accessible (e.g., `/api/chat`).

---

## Environment Variables
- Never commit your `.env` file or API keys to git.
- Use Vercel's environment variable settings for production.

---

## Security Notes
- `.env` and `api/.env` are in `.gitignore` by default.
- Never share your API key publicly.

---

## Customization
- You can modify the backend to add a system prompt or other logic as needed.
- The frontend is easily customizable for your brand or use case.

---

## License
MIT
