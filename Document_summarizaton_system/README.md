# Document Summarization System (Synopsis)

Industry-style document summarization platform with a Django API and a React SPA. It extracts text from multiple formats, applies OCR when needed, and generates structured summaries using a local LLM via Ollama. Includes user auth, credits, payment top-ups, and upload history.

## Highlights

- Multi-format ingestion: PDF, TXT, DOCX, PNG/JPG
- OCR fallback for scanned PDFs and image uploads (Tesseract + pdf2image)
- Local LLM summarization via Ollama with structured output
- Image description fallback using BLIP (torch/transformers) for non-text images
- Preflight credit estimation before summarization
- Streaming summarization (SSE) option
- Session-based auth, profile management, OTP-based password reset, and Google OAuth
- Credits system with Razorpay top-ups (test mode)
- Upload history, detail view, and file download

## Tech Stack

- Backend: Django 4.2, SQLite, session auth
- Frontend: React 19 + Vite + React Router
- LLM: Ollama (local)
- OCR: pdfplumber, PyPDF2, pdf2image, Tesseract, Pillow
- Payments: Razorpay (test mode)

## Project Structure

- Document_summarizaton_system/ - Django project settings and entrypoints
- DSS_app/ - Django app (API endpoints, OCR, summarization, auth, payments)
- frontend/ - React SPA
- db.sqlite3 - Local development database

## Prerequisites

### Backend

- Python 3.10+ recommended
- Pip dependencies:

```bash
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

### Ollama (local LLM)

1. Install Ollama: https://ollama.com
2. Pull a model (one-time):

```bash
ollama pull mistral
```

3. Ensure Ollama is running (default endpoint: http://localhost:11434).

### OCR dependencies (optional but recommended)

- Tesseract installed and on PATH
- Poppler (for pdf2image) installed and on PATH

### Image captioning (optional)

Image description fallback uses BLIP:

```bash
pip install torch transformers
```

## Run Locally

### Backend (Django)

```bash
python manage.py runserver
```

### Frontend (Vite)

```bash
cd frontend
npm run dev
```

## Configuration

You can set environment variables via shell or a .env file at the project root.

### LLM (Ollama)

- DSS_OLLAMA_MODEL (default: mistral)
- DSS_OLLAMA_HOST (default: http://localhost:11434)
- DSS_OLLAMA_MAX_CHARS (default: 12000)
- DSS_OLLAMA_TEMPERATURE (default: 0.2)
- DSS_OLLAMA_NUM_PREDICT (default: 280)
- DSS_OLLAMA_NUM_CTX (default: 1536)
- DSS_OLLAMA_TOP_P (default: 0.9)
- DSS_OLLAMA_MAX_CONCURRENCY (default: 1)
- DSS_OLLAMA_SLOT_WAIT_TIMEOUT (default: 20)
- DSS_OLLAMA_REQUEST_TIMEOUT (default: 90)
- DSS_SUMMARY_CACHE_MAX_ITEMS (default: 24)

### OCR

- DSS_OCR_MAX_PAGES (default: 12)
- DSS_OCR_DPI (default: 220)

### Image captioning (BLIP)

- DSS_BLIP_MODEL (default: Salesforce/blip-image-captioning-base)
- DSS_BLIP_MAX_NEW_TOKENS (default: 80)

### Auth and Google OAuth

- DSS_GOOGLE_CLIENT_ID
- DSS_GOOGLE_CLIENT_SECRET
- DSS_GOOGLE_REDIRECT_URI (default: http://localhost:8000/api/auth/google/callback/)
- DSS_FRONTEND_BASE (default: http://localhost:5173)

### Email (OTP delivery)

- EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
- EMAIL_USE_TLS, EMAIL_USE_SSL, EMAIL_TIMEOUT
- DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME
- DSS_OTP_ECHO (dev helper: echo OTP in response when SMTP fails)
- DSS_PW_OTP_TTL_SECONDS, DSS_PW_OTP_COOLDOWN_SECONDS, DSS_PW_OTP_MAX_ATTEMPTS

### Razorpay (test mode)

- DSS_RAZORPAY_KEY_ID
- DSS_RAZORPAY_KEY_SECRET

## Core API Endpoints

Auth:

- POST /api/auth/signup/
- POST /api/auth/login/
- GET /api/auth/me/
- POST /api/auth/logout/
- POST /api/auth/change-password/
- POST /api/auth/change-password/otp/request/
- POST /api/auth/change-password/otp/verify/
- GET /api/auth/google/login/
- GET /api/auth/google/callback/

Summarization:

- POST /api/uploads/preflight/
- POST /api/uploads/<upload_id>/summarize/
- POST /api/summarize/ (direct summarize)
- POST /api/summarize/stream/ (SSE streaming)

Uploads:

- GET /api/uploads/
- GET /api/uploads/<upload_id>/
- GET /api/uploads/<upload_id>/download/

Payments (Razorpay):

- GET /api/payments/razorpay/config/
- POST /api/payments/razorpay/create-order/
- POST /api/payments/razorpay/verify/

## Credits and Billing

Credits are calculated from extracted text size (UTF-8 bytes), not raw file size. The UI uses a preflight call to estimate required credits before summarization. If credits are insufficient, the summary can still be generated and displayed, but it will not be saved until credits are available. Razorpay top-ups are supported in test mode.

## Storage

Uploaded files are stored as BLOBs in SQLite along with extracted text and summaries. Each user can list, view, and download their own uploads.

## Troubleshooting

- Ollama not running: summaries will fail with a 503. Start Ollama and retry.
- OCR not working: ensure Tesseract and Poppler are installed and on PATH.
- DOCX extraction missing: install python-docx.
- OTP emails not arriving: configure SMTP or enable DSS_OTP_ECHO=1 for local testing.

## Development Notes

- CORS is configured for the local Vite dev server (localhost:5173).
- Session cookies use SameSite=Lax to work across local origins.

## Git Basics (quick reminder)

```bash
git status
git add .
git commit -m "A descriptive commit message"
git push origin main
```
