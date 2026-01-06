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
git push
```
