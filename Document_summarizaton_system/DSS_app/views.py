from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import PyPDF2
import io
import logging

logger = logging.getLogger(__name__)


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
    Only PDF files are processed using PyPDF2.
    Other file types are not handled.
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

        # Parse PDF
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

        # Extract text from all pages
        extracted_text = ""
        for page_num in range(num_pages):
            try:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                continue

        # Check if text was extracted
        if not extracted_text.strip():
            logger.warning("No text could be extracted from PDF")
            response = JsonResponse({
                'error': 'No text could be extracted from the PDF. The PDF might be scanned or image-based.'
            }, status=400)
            return add_cors_headers(response)

        logger.info(f"Text extracted successfully. Length: {len(extracted_text)} characters")

        # For now, return the extracted text as summary
        # TODO: Add summarization logic here later
        summary = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text

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
