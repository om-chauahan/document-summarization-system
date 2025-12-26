from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import io
import logging

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
            return ""

        try:
            # Use a moderate DPI for accuracy; higher DPI = slower/more memory.
            images = convert_from_bytes(pdf_bytes, dpi=250)
            ocr_parts: list[str] = []
            for img in images:
                ocr_txt = pytesseract.image_to_string(img) or ""
                ocr_txt = _normalize_text(ocr_txt)
                if ocr_txt:
                    ocr_parts.append(ocr_txt)
            text = _normalize_text("\n\n".join(ocr_parts))
        except Exception:
            text = ""

    return text


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

        # Check if text was extracted
        if not extracted_text.strip():
            logger.warning("No text could be extracted from PDF")
            response = JsonResponse({
                'error': 'No text could be extracted from the PDF. If it is scanned, enable/install OCR dependencies (pytesseract + pdf2image) and ensure Tesseract is installed.'
            }, status=400)
            return add_cors_headers(response)

        logger.info(f"Text extracted successfully. Length: {len(extracted_text)} characters")

        # Return full extracted text (no truncation). If you later add summarization,
        # implement it here and keep `extracted_text` available separately.
        summary = extracted_text

        response = JsonResponse({
            'success': True,
            'summary': summary,
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
