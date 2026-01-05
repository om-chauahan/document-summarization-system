from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import io
import logging
import os
import shutil
import re

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
    from .summarization import summarize_text as model_summarize_text, generate_best_summary
except Exception:  # pragma: no cover
    model_summarize_text = None
    generate_best_summary = None


def _normalize_text(text: str) -> str:
    """Light normalization to reduce whitespace noise."""
    return "\n".join(line.rstrip() for line in (text or "").splitlines()).strip()


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


def _extract_key_facts(text: str) -> list[str]:
    """Extract short factual lines (IDs, numbers, identifiers, emails) that
    should be preserved in summaries.

    Returns a list of short strings like 'ABC ID: 430050715592'.
    """
    if not text:
        return []

    facts = []

    # Look for explicit 'ABC ID' patterns
    for m in re.finditer(r"\bABC\s*ID\b[:\s]*([A-Za-z0-9-]+)", text, flags=re.IGNORECASE):
        v = m.group(1).strip()
        facts.append(f"ABC ID: {v}")

    # Aadhaar-like numbers (12 digits) and other long numeric IDs
    for m in re.finditer(r"\b(\d{9,16})\b", text):
        v = m.group(1)
        # avoid picking up page numbers or short numbers
        if len(v) >= 9:
            facts.append(f"ID: {v}")

    # Emails
    for m in re.finditer(r"[\w.-]+@[\w.-]+\.[A-Za-z]{2,}", text):
        facts.append(m.group(0))

    # Short unique tokens like 'Powered by DigiLocker' or 'DigiLocker'
    if "digilocker" in text.lower():
        facts.append("DigiLocker reference present")

    # Deduplicate while preserving order
    seen = set()
    out = []
    for f in facts:
        if f not in seen:
            seen.add(f)
            out.append(f)

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
    Only PDF files are supported.
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

        # Check if file is PDF
        if not file_name.endswith('.pdf'):
            logger.warning(f"Non-PDF file attempted: {file_name}")
            response = JsonResponse({
                'error': 'Only PDF files are supported. Other formats are not implemented yet.'
            }, status=400)
            return add_cors_headers(response)

        # Check file size (limit to 50MB)
        if uploaded_file.size > 50 * 1024 * 1024:
            logger.warning(f"File too large: {uploaded_file.size} bytes")
            response = JsonResponse({
                'error': 'File size exceeds 50MB limit'
            }, status=400)
            return add_cors_headers(response)

        # Read the PDF file
        try:
            pdf_file = uploaded_file.read()
            if not pdf_file:
                logger.warning("Empty file uploaded")
                response = JsonResponse({
                    'error': 'File is empty'
                }, status=400)
                return add_cors_headers(response)
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            response = JsonResponse({
                'error': f'Error reading file: {str(e)}'
            }, status=400)
            return add_cors_headers(response)

        # Validate PDF structure early (quick check for totally invalid files)
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
            num_pages = len(pdf_reader.pages)
            logger.info(f"PDF parsed successfully. Pages: {num_pages}")
        except PyPDF2.errors.PdfReadError as e:
            logger.error(f"Invalid PDF file: {str(e)}")
            response = JsonResponse({
                'error': f'Invalid PDF file: {str(e)}'
            }, status=400)
            return add_cors_headers(response)

        # Extract text using a higher-accuracy pipeline
        extracted_text = extract_text_from_pdf_bytes(pdf_file, ocr_if_needed=True)

        # Normalize spacing / line-wrapping issues so display and summarization are cleaner.
        try:
            extracted_text = normalize_extracted_text(extracted_text)
        except Exception:
            # Don't fail extraction for normalization issues; log and continue with raw text.
            logger.exception("Failed to normalize extracted text")

        # Check if text was extracted
        if not extracted_text.strip():
            logger.warning("No text could be extracted from PDF")
            response = JsonResponse({
                'error': 'No text could be extracted from the PDF. If it is scanned, enable/install OCR dependencies (pytesseract + pdf2image) and ensure Tesseract is installed.'
            }, status=400)
            return add_cors_headers(response)

        logger.info(f"Text extracted successfully. Length: {len(extracted_text)} characters")

        # Build an improved summary. Prefer a deterministic structured summary first
        # (preserves IDs/dates). If that function isn't available, fall back to the
        # model summarizer (if installed). If neither is available, return 503.
        summary = ""
        summarization_used = False

        if generate_best_summary is not None:
            try:
                summary = generate_best_summary(extracted_text)
                summarization_used = True
            except Exception:
                logger.exception("Structured summary generation failed; will try model summarizer as fallback")

        if not summarization_used:
            # Try model summarizer if present
            if model_summarize_text is None:
                logger.warning("Summarization unavailable (missing transformers dependencies)")
                response = JsonResponse({
                    'error': 'Summarization is not available on the server. Please install transformers and its dependencies (see README).'
                }, status=503)
                response = add_cors_headers(response)
                return response
            try:
                summary = model_summarize_text(extracted_text)
                summarization_used = True
            except Exception as e:
                logger.error("Model summarization failed: %s", str(e), exc_info=True)
                response = JsonResponse({
                    'error': f'Summarization failed: {str(e)}'
                }, status=500)
                response = add_cors_headers(response)
                return response

        # Ensure short factual items are visible to the user. The structured summary
        # should already include IDs, but we keep this guard in case a model summary
        # was used and omitted small facts.
        try:
            key_facts = _extract_key_facts(extracted_text)
            if key_facts:
                missed = [f for f in key_facts if f not in (summary or "")]
                if missed:
                    facts_block = "Key facts:\n" + "\n".join(missed) + "\n\n"
                    summary = facts_block + (summary or "")
        except Exception:
            logger.exception("Failed to extract/preserve key facts for summary")

        response = JsonResponse({
            'success': True,
            'extracted_text': extracted_text,
            'summary': summary,
            'summarization_used': summarization_used,
            'extracted_text_length': len(extracted_text),
            'message': 'PDF text extracted successfully'
        }, status=200)
        return add_cors_headers(response)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        response = JsonResponse({
            'error': f'An error occurred while processing the file: {str(e)}'
        }, status=500)
        return add_cors_headers(response)
