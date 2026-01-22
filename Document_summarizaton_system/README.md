## Document Summarization System

Uploads a PDF, extracts text (including OCR fallback), and generates a formatted summary using a **local LLM via Ollama**.

## Prerequisites

### Ollama (local LLM)

1. Install Ollama: https://ollama.com
2. Pull the model (one-time):

```bash
ollama pull mistral
```

3. Make sure Ollama is running (default endpoint: `http://localhost:11434`).

### Python dependencies

Install backend requirements:

```bash
pip install -r requirements.txt
```

## Run

### Backend (Django)

```bash
python3 manage.py runserver
```

### Frontend (Vite/React)

```bash
cd frontend
npm install
npm run dev
```

## Configuration (optional)

Environment variables:

- `DSS_OLLAMA_MODEL` (default: `mistral`)
- `DSS_OLLAMA_HOST` (default: `http://localhost:11434`)
- `DSS_OLLAMA_MAX_CHARS` (default: `12000`) — lower = faster summaries on laptops
- `DSS_OLLAMA_TEMPERATURE` (default: `0.2`)
- `DSS_OLLAMA_NUM_PREDICT` (default: `280`) — lower = faster but shorter output
- `DSS_OLLAMA_NUM_CTX` (default: `1536`) — lower = faster but less context
- `DSS_OLLAMA_TOP_P` (default: `0.9`)

### Google OAuth (Continue with Google)

This project supports a **server-side Google OAuth** flow (Authorization Code) using Django sessions.

#### 1) Create OAuth Client in Google Cloud Console

- Go to **Google Cloud Console** → APIs & Services → **OAuth consent screen**
  - Choose **External**
  - Fill app info
  - Add test users (for development)
- Then go to **Credentials** → **Create Credentials** → **OAuth client ID**
  - Application type: **Web application**
  - **Authorized JavaScript origins**:
    - `http://localhost:5173`
    - `http://127.0.0.1:5173`
  - **Authorized redirect URIs**:
    - `http://127.0.0.1:8000/api/auth/google/callback/`
    - (optional) `http://localhost:8000/api/auth/google/callback/`

#### 2) Set environment variables (backend)

Set these before running Django (either export them in your shell or copy `.env.example` → `.env` and fill it in):

```bash
export DSS_GOOGLE_CLIENT_ID="<your-client-id>"
export DSS_GOOGLE_CLIENT_SECRET="<your-client-secret>"
export DSS_GOOGLE_REDIRECT_URI="http://127.0.0.1:8000/api/auth/google/callback/"
export DSS_FRONTEND_BASE="http://localhost:5173"
```

#### 3) Use it in the UI

The **Continue with Google** buttons on **Login** and **Signup** redirect to:

- `GET /api/auth/google/login/?next=/upload`

After successful login, the backend redirects the browser to the `next` frontend path.

### Performance tips (MacBooks / low-lag)

- If your Mac starts lagging during summarization, reduce input + output:
  - Set `DSS_OLLAMA_MAX_CHARS=8000`
  - Set `DSS_OLLAMA_NUM_PREDICT=200`
  - Set `DSS_OLLAMA_NUM_CTX=1024`
- The app already does a lightweight pre-compression before sending text to the LLM,
  but these knobs can reduce load further.

## Git basics (quick reminder)

```bash
git status
git add .
git commit -m "A descriptive commit message"
git push origin main
```
