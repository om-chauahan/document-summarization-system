# Project Report Editing Context

This file is a faster-to-edit companion for the main report. Use it when you want to customize the final report before converting it to PDF.

## 1. Final Project Title Options

Choose one title and keep it consistent everywhere:

1. Synopsis: AI-Powered Document Summarization System
2. Intelligent Document Summarization and OCR Platform
3. Secure Multi-Format Document Summarization System
4. AI-Based Document Analysis and Summarization Platform

Recommended title: **Synopsis: AI-Powered Document Summarization System**

## 2. Ready-to-Use Abstract

The Document Summarization System, titled Synopsis, is a full-stack web application developed to simplify the process of understanding large and complex documents. The system allows users to upload files in formats such as PDF, TXT, DOCX, PNG, and JPG, extracts readable text through parser-based and OCR-based techniques, and generates structured summaries using a local Large Language Model powered by Ollama. In addition to summarization, the platform provides secure user authentication, upload history management, profile and security controls, a credit-based usage model, and Razorpay-based payment support for top-ups. The project demonstrates the practical integration of modern web development, document processing, OCR, and local AI inference into a single industry-style software solution.

## 3. Ready-to-Use Introduction

In modern academic, business, and administrative workflows, users frequently deal with lengthy reports, notes, legal documents, and scanned records. Reading such content manually consumes significant time and often reduces productivity. The main purpose of this project is to design a document summarization platform that can automatically extract important textual information from multiple file types and provide a concise, readable summary. The proposed system, Synopsis, bridges the gap between AI-based summarization and real-world software usability by combining file upload, OCR fallback, local LLM summarization, secure login, user-specific history, and payment-backed credit management in one integrated platform.

## 4. Short Problem Statement

Users often need only the key information from large documents, but manual reading is time-consuming and inefficient. Existing tools may fail on scanned files, support limited formats, or provide no user management and history tracking. Therefore, a practical, secure, and multi-format summarization system is required.

## 5. Objectives Text

- To build a web-based document summarization platform.
- To support multi-format file upload including PDF, TXT, DOCX, PNG, and JPG.
- To perform OCR for scanned and image-based documents.
- To generate structured summaries using a local AI model.
- To maintain user-wise upload history and stored summaries.
- To implement secure authentication and protected access.
- To include a credit-based usage and payment top-up mechanism.

## 6. Architecture Explanation Text

The architecture of the system is divided into three primary layers: presentation layer, application layer, and data/AI services layer. The presentation layer is implemented using React and manages user interaction, routing, and display of summaries and uploads. The application layer is implemented using Django and exposes APIs for authentication, summarization, uploads, billing, and security. The data and AI services layer includes SQLite for persistence, OCR tools for extraction from scanned documents, and Ollama for local large language model inference.

## 7. Frontend Description Text

The frontend is developed using React with Vite and React Router. It includes both public pages and protected pages. Public pages handle awareness and authentication, while protected pages allow users to upload documents, manage their profile, purchase credits, and access their upload history. The user interface is designed to present the summarization workflow clearly and maintain a professional application feel.

## 8. Backend Description Text

The backend is developed in Django and handles all core business logic. It validates requests, authenticates users using Django sessions, processes uploaded files, extracts text, coordinates summarization, calculates credits, manages payment workflows, and stores results in the database. The backend is organized to keep file handling, auth operations, and billing operations manageable and extensible.

## 9. OCR and AI Pipeline Text

The project uses a layered extraction pipeline to maximize robustness. PDFs are first processed through direct extraction libraries. If the file is scanned or image-based, the pages are converted to images and passed through OCR using Tesseract. After text normalization, the processed content is summarized through a locally hosted Ollama model. This approach ensures that the system remains useful even for non-standard and scanned inputs.

## 10. Conclusion Text

The Synopsis project successfully demonstrates a production-inspired implementation of AI-assisted document summarization. It combines document processing, OCR, summarization, secure user management, payment-backed credits, and historical record keeping into a single working software solution. The system is not only academically relevant but also practically useful for real document-heavy workflows.

## 11. Viva / Professor Discussion Points

Use these if your professor asks what makes the project strong:

- The project is not just an AI demo; it is a complete software product with auth, history, billing, and admin support.
- It supports both text-based and scanned documents through OCR fallback.
- It uses a local LLM through Ollama, which improves privacy and reduces dependence on external APIs.
- The architecture is modular and can be extended to stronger databases and cloud deployment.
- The credit and payment system adds practical product thinking to the solution.

## 12. Personalization Checklist

Replace the following before final submission:

- [Student Name 1], [Student Name 2], [Student Name 3]
- Enrollment IDs
- Guide name
- HOD name
- University name
- Department format required by your college
- Real screenshots from your application
- Actual dates and signatures

## 13. Recommended Formatting for Final PDF

- Font for headings: Times New Roman Bold, 16-18 pt
- Font for body: Times New Roman, 12 pt
- Line spacing: 1.5
- Alignment: Justified body text
- Section numbering: Use 1, 1.1, 1.2 style
- Add page numbers in footer
- Add figure captions under screenshots
- Add table captions above each table

## 14. Final Submission Advice

If you want the report to look professional in front of your professor:

- Add 6 to 10 real screenshots from your application
- Keep the report around 20 to 30 pages after formatting
- Insert one architecture diagram and one database diagram
- Keep wording formal and technical, not casual
- Mention real engineering decisions such as OCR fallback, local LLM, credits, and secure routes