# 2025-26_Sdp3_Document-summarization-system
# in ls output where manage.py available from there use git command to push

📌 Project Overview
The Document Summarization System is a Django-based web application that allows users to upload documents (PDF / DOCX) and automatically generate concise summaries using Natural Language Processing (NLP) techniques.
The system is designed with a clear separation of concerns:
Frontend for file upload and result display
Backend for text extraction, processing, and summarization
Machine Learning model for generating summaries (local, no external API)

✅ Frontend (Django Templates)
Basic frontend UI created using Django templates
File upload form implemented
Summary output section added
Frontend communicates with backend using JavaScript (fetch API)
📁 Location:
DSS_app/templates/DSS_app/

✅ Backend (Django Views)
Django views configured to handle:
File upload requests
API endpoint for summarization
URL routing set up between frontend and backend
📁 Location:
DSS_app/views.py
DSS_app/urls.py

✅ Text Extraction Setup
PyPDF2 – extract text from text-based PDFs
python-docx – extract text from DOCX files
pytesseract + Tesseract OCR – extract text from scanned PDFs / images
pdf2image & Pillow – convert PDF pages to images for OCR

✅ Machine Learning Model
Selected summarization model:
facebook/bart-large-cnn
Understanding of:
Text cleaning
Token-based chunking
Hierarchical summarization

🧠 System Architecture (Current Design)

User Uploads File

        User Uploads File


Django Frontend (HTML + JavaScript)

        Django Frontend (HTML + JavaScript)


Django Backend (views.py)

        Django Backend (views.py)

Text Extraction (PDF / DOCX / OCR)

        Text Extraction (PDF / DOCX / OCR)

Text Cleaning & Chunking

        Text Cleaning & Chunking

Summarization Model (BART – local)

        Summarization Model (BART – local)

Summary Displayed to User

         Summary Displayed to User





