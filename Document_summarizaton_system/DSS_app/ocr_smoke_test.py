"""Quick OCR smoke test for scanned PDFs.

Run it inside the same environment as Django to verify:
- pdf2image can render PDF bytes (poppler available)
- pytesseract can OCR the rendered image (tesseract available)

Usage (from project root where manage.py lives):
  python DSS_app/ocr_smoke_test.py /path/to/scanned.pdf

This script is intentionally lightweight and doesn't depend on Django settings.
"""

from __future__ import annotations

import sys

from DSS_app.views import extract_text_from_pdf_bytes


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python DSS_app/ocr_smoke_test.py /path/to/file.pdf")
        return 2

    pdf_path = sys.argv[1]
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    text = extract_text_from_pdf_bytes(pdf_bytes, ocr_if_needed=True)
    print(f"Extracted length: {len(text)}")
    if text:
        preview = text[:1000].replace("\n", "\\n")
        print(f"Preview (first 1000 chars): {preview}")
        return 0

    print("No text extracted.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
