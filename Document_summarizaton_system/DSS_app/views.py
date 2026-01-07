from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import io
import logging
import os
import shutil
import re

try:
    from docx import Document as DocxDocument
except Exception:  # pragma: no cover
    DocxDocument = None

import PyPDF2

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None

try:
    from pdf2image import convert_from_bytes
except Exception:  # pragma: no cover
    convert_from_bytes = None

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None

logger = logging.getLogger(__name__)

try:
    # Local LLM summarization via Ollama.
    from .summarization import summarize_text as model_summarize_text
    from .summarization import stream_summary as model_stream_summary
except Exception:  # pragma: no cover
    model_summarize_text = None
    model_stream_summary = None


def _normalize_text(text: str) -> str:
    """Light normalization to reduce whitespace noise."""
    return "\n".join(line.rstrip() for line in (text or "").splitlines()).strip()


def extract_text_from_txt_bytes(raw: bytes) -> str:
    """Extract text from a plain text file.

    Tries UTF-8 first, then falls back to latin-1 as a last resort.
    """
    if not raw:
        return ""
    try:
        return _normalize_text(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return _normalize_text(raw.decode("latin-1", errors="ignore"))


def extract_text_from_docx_bytes(raw: bytes) -> str:
    """Extract text from a .docx file using python-docx."""
    if not raw:
        return ""
    if DocxDocument is None:
        logger.warning("DOCX extraction skipped (python-docx not installed)")
        return ""

    try:
        doc = DocxDocument(io.BytesIO(raw))
        parts: list[str] = []
        for p in doc.paragraphs:
            t = (p.text or "").strip()
            if t:
                parts.append(t)
        return _normalize_text("\n".join(parts))
    except Exception:
        logger.exception("DOCX extraction failed")
        return ""


def extract_text_from_image_bytes(raw: bytes) -> str:
    """Extract text from an image via OCR (png/jpg/jpeg)."""
    if not raw:
        return ""
    if pytesseract is None:
        logger.warning("Image OCR skipped (pytesseract not installed)")
        return ""

    try:
        from PIL import Image

        img = Image.open(io.BytesIO(raw))
        txt = pytesseract.image_to_string(img, config="--oem 3 --psm 6") or ""
        return _normalize_text(txt)
    except Exception:
        logger.exception("Image OCR failed")
        return ""


def extract_text_from_uploaded_file(uploaded_file) -> tuple[str, str]:
    """Extract text from an uploaded file.

    Returns: (extracted_text, detected_type)
    """
    name = (uploaded_file.name or "").lower()
    raw = uploaded_file.read()

    if name.endswith(".pdf"):
        text = extract_text_from_pdf_bytes(raw, ocr_if_needed=True)
        return text, "pdf"

    if name.endswith(".txt"):
        return extract_text_from_txt_bytes(raw), "txt"

    if name.endswith(".docx"):
        return extract_text_from_docx_bytes(raw), "docx"

    if name.endswith((".png", ".jpg", ".jpeg")):
        return extract_text_from_image_bytes(raw), "image"

    return "", "unsupported"


def extract_text_from_pdf_bytes(pdf_bytes: bytes, *, ocr_if_needed: bool = True) -> str:
    """Extract text from PDFs.

    Strategy:
    1) Use `pdfplumber` when available (better layout/text extraction than PyPDF2 in many PDFs).
    2) Fallback to PyPDF2 if pdfplumber isn't installed or fails.
    3) If still empty and OCR is enabled, render pages to images and OCR with Tesseract.

    Returns normalized text (may be empty if nothing extractable and OCR unavailable).
    """
    if not pdf_bytes:
        return ""

    extracted_parts: list[str] = []

    # 1) pdfplumber first (best quality for many text-based PDFs)
    if pdfplumber is not None:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    # x_tolerance/y_tolerance can improve spacing in some docs.
                    txt = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                    txt = _normalize_text(txt)
                    if txt:
                        extracted_parts.append(txt)
        except Exception:
            extracted_parts = []

    text = _normalize_text("\n\n".join(extracted_parts))

    # 2) Fallback to PyPDF2
    if not text:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            for page in pdf_reader.pages:
                page_text = page.extract_text() or ""
                page_text = _normalize_text(page_text)
                if page_text:
                    extracted_parts.append(page_text)
            text = _normalize_text("\n\n".join(extracted_parts))
        except Exception:
            text = ""

    # 3) OCR fallback for scanned PDFs
    if ocr_if_needed and not text:
        if convert_from_bytes is None or pytesseract is None:
            logger.warning(
                "OCR fallback skipped because dependencies are missing: convert_from_bytes=%s pytesseract=%s",
                convert_from_bytes is not None,
                pytesseract is not None,
            )
            return ""

        try:
            # Helpful diagnostics: poppler + tesseract availability.
            poppler_hint = shutil.which("pdftoppm") or shutil.which("pdfinfo")
            tesseract_cmd = shutil.which("tesseract")
            logger.info(
                "OCR fallback starting (poppler=%s, tesseract=%s, TESSERACT_CMD=%s)",
                poppler_hint,
                tesseract_cmd,
                getattr(pytesseract.pytesseract, "tesseract_cmd", None),
            )

            # Use a moderate DPI for accuracy; higher DPI = slower/more memory.
            images = convert_from_bytes(pdf_bytes, dpi=250)
            logger.info("OCR fallback rendered %s page image(s)", len(images))
            ocr_parts: list[str] = []
            for img in images:
                # Better defaults for typical scanned documents.
                # psm 6 = assume a single uniform block of text.
                ocr_txt = pytesseract.image_to_string(img, config="--oem 3 --psm 6") or ""
                ocr_txt = _normalize_text(ocr_txt)
                if ocr_txt:
                    ocr_parts.append(ocr_txt)
            text = _normalize_text("\n\n".join(ocr_parts))
            if not text:
                logger.warning(
                    "OCR completed but produced empty text (rendered_pages=%s, tesseract=%s)",
                    len(images) if "images" in locals() else None,
                    tesseract_cmd,
                )
        except Exception as e:
            logger.error("OCR fallback failed: %s", str(e), exc_info=True)
            text = ""

    return text


def normalize_extracted_text(text: str) -> str:
    """Normalize extracted PDF text for display and summarization.

    - normalize newlines
    - collapse multiple spaces/tabs
    - join lines inside a paragraph when they are line-wrapped (heuristic)
    - preserve paragraph breaks (keep at most one blank line between paragraphs)
    """
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse tabs/spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Split into paragraphs (two or more newlines separate paragraphs)
    paras = re.split(r"\n{2,}", text)
    normalized_paras = []

    for p in paras:
        # split by single newlines (these are likely line wraps)
        lines = [ln.strip() for ln in p.split("\n") if ln.strip()]
        if not lines:
            continue

        # Reconstruct paragraph: join lines that look like they were wrapped.
        cur = lines[0]
        for ln in lines[1:]:
            # If the current line ends with a sentence terminator, keep newline.
            if re.search(r"[\.\?\!:\"]$", cur):
                cur = cur + "\n" + ln
                continue

            # If the next line starts with a bullet/number or is all-caps (heading), keep newline.
            if re.match(r"^[-•\*\d+]", ln) or re.match(r"^[A-Z\s]{3,}$", ln):
                cur = cur + "\n" + ln
                continue

            # Otherwise it's likely a line-wrap: join with a space.
            cur = cur + " " + ln

        normalized_paras.append(cur.strip())

    # Re-join paragraphs with a single blank line.
    out = "\n\n".join(normalized_paras)
    # Finally, collapse any accidental >2 newlines to two, and strip edges.
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def add_cors_headers(response):
    """Add CORS headers to response"""
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def summarize_document(request):
    """
    API endpoint to handle document upload and extract text from PDF files.
    Supported formats: PDF, TXT, DOCX, and images (PNG/JPG) via OCR.
    """
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response)

    try:
        # Check if file is present in request
        if 'file' not in request.FILES:
            logger.warning("No file provided in request")
            response = JsonResponse({
                'error': 'No file provided'
            }, status=400)
            return add_cors_headers(response)

        uploaded_file = request.FILES['file']
        
        # Check if file has a name
        if not uploaded_file.name:
            logger.warning("File has no name")
            response = JsonResponse({
                'error': 'File has no name'
            }, status=400)
            return add_cors_headers(response)

        file_name = uploaded_file.name.lower()
        logger.info(f"Processing file: {file_name}, Size: {uploaded_file.size} bytes")

        # We support multiple formats now; file-type validation happens during extraction.

        # Check file size (limit to 50MB)
        if uploaded_file.size > 50 * 1024 * 1024:
            logger.warning(f"File too large: {uploaded_file.size} bytes")
            response = JsonResponse({
                'error': 'File size exceeds 50MB limit'
            }, status=400)
            return add_cors_headers(response)

        # Extract text based on file type
        extracted_text, detected_type = extract_text_from_uploaded_file(uploaded_file)

        if detected_type == "unsupported":
            response = JsonResponse(
                {
                    'error': 'Unsupported file type. Supported: PDF, TXT, DOCX, PNG/JPG (OCR).'
                },
                status=400,
            )
            return add_cors_headers(response)

        if not extracted_text.strip():
            if detected_type == "docx" and DocxDocument is None:
                msg = 'DOCX support is not available on the server. Please install python-docx.'
            elif detected_type == "image" and pytesseract is None:
                msg = 'Image OCR is not available on the server. Please install pytesseract and ensure Tesseract is installed.'
            else:
                msg = 'No text could be extracted from the file.'
            response = JsonResponse({'error': msg}, status=400)
            return add_cors_headers(response)

        # Normalize spacing / line-wrapping issues so display and summarization are cleaner.
        try:
            extracted_text = normalize_extracted_text(extracted_text)
        except Exception:
            # Don't fail extraction for normalization issues; log and continue with raw text.
            logger.exception("Failed to normalize extracted text")

        # Check if text was extracted after normalization
        if not extracted_text.strip():
            response = JsonResponse({'error': 'No text could be extracted from the file.'}, status=400)
            return add_cors_headers(response)

        logger.info(f"Text extracted successfully. Length: {len(extracted_text)} characters")

        # Summarize using local Ollama model.
        if model_summarize_text is None:
            logger.warning("Summarization unavailable (missing ollama dependency)")
            response = JsonResponse({
                'error': 'Summarization is not available on the server. Please install the ollama python package and ensure Ollama is running (see README).'
            }, status=503)
            response = add_cors_headers(response)
            return response

        try:
            summary = model_summarize_text(extracted_text)
        except Exception as e:
            logger.error("Model summarization failed: %s", str(e), exc_info=True)
            response = JsonResponse({
                'error': f'Summarization failed: {str(e)}'
            }, status=500)
            response = add_cors_headers(response)
            return response

        response = JsonResponse({
            'success': True,
            'extracted_text': extracted_text,
            'summary': summary,
            'summarization_used': True,
            'extracted_text_length': len(extracted_text),
            'detected_type': detected_type,
            'message': 'Document text extracted successfully'
        }, status=200)
        return add_cors_headers(response)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        response = JsonResponse({
            'error': f'An error occurred while processing the file: {str(e)}'
        }, status=500)
        return add_cors_headers(response)


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def summarize_document_stream(request):
    """Streaming API endpoint (SSE) to reduce perceived lag.

    Returns a Server-Sent Events stream:
    - event: meta  (JSON metadata, once)
    - event: token (incremental text)
    - event: done  (signals completion)
    - event: error (signals error)
    """

    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response)

    if 'file' not in request.FILES:
        response = JsonResponse({'error': 'No file provided'}, status=400)
        return add_cors_headers(response)

    uploaded_file = request.FILES['file']
    if not uploaded_file.name:
        response = JsonResponse({'error': 'File has no name'}, status=400)
        return add_cors_headers(response)

    if model_stream_summary is None:
        response = JsonResponse(
            {
                'error': 'Streaming summarization is not available on the server. Please install ollama and ensure Ollama is running.'
            },
            status=503,
        )
        return add_cors_headers(response)

    extracted_text, detected_type = extract_text_from_uploaded_file(uploaded_file)

    if detected_type == "unsupported":
        response = JsonResponse(
            {
                'error': 'Unsupported file type. Supported: PDF, TXT, DOCX, PNG/JPG (OCR).'
            },
            status=400,
        )
        return add_cors_headers(response)
    try:
        extracted_text = normalize_extracted_text(extracted_text)
    except Exception:
        logger.exception("Failed to normalize extracted text")

    if not extracted_text.strip():
        if detected_type == "docx" and DocxDocument is None:
            msg = 'DOCX support is not available on the server. Please install python-docx.'
        elif detected_type == "image" and pytesseract is None:
            msg = 'Image OCR is not available on the server. Please install pytesseract and ensure Tesseract is installed.'
        else:
            msg = 'No text could be extracted from the file.'
        response = JsonResponse({'error': msg}, status=400)
        return add_cors_headers(response)

    def sse_pack(event: str, data: str) -> str:
        # SSE format: event + data lines + blank line
        # Ensure data has no bare CR.
        safe = (data or "").replace("\r", "")
        lines = safe.split("\n")
        payload = "\n".join(f"data: {ln}" for ln in lines)
        return f"event: {event}\n{payload}\n\n"

    def event_stream():
        # Send metadata early so the UI can show extracted length.
        meta_json = (
            '{'
            f'"extracted_text_length": {len(extracted_text)},'
            f'"detected_type": "{detected_type}",'
            '"summarization_used": true'
            '}'
        )
        yield sse_pack("meta", meta_json)

        try:
            for chunk in model_stream_summary(extracted_text):
                # Send tokens/chunks as they arrive.
                yield sse_pack("token", chunk)
            # Send extracted text at the end so the UI doesn't need a second upload.
            # Remove carriage returns to keep the SSE framing safe.
            yield sse_pack("extracted", extracted_text)
            yield sse_pack("done", "")
        except Exception as e:
            yield sse_pack("error", str(e))

    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"  # helps avoid buffering on some proxies
    return add_cors_headers(resp)
