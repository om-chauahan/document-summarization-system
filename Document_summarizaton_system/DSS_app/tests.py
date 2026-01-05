from __future__ import annotations

from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch


class SummarizationHelpersTests(TestCase):
	def test_chunking_produces_multiple_chunks(self):
		from DSS_app.summarization import _chunk_text_by_tokens

		class DummyTokenizer:
			def encode(self, text, add_special_tokens=False):
				# approximate 1 token per 4 characters
				return [0] * max(1, len(text) // 4)

		text = "A" * 9500
		tok = DummyTokenizer()
		chunks = _chunk_text_by_tokens(text, tok, chunk_tokens=800, overlap_tokens=50)
		self.assertGreaterEqual(len(chunks), 3)


class SummarizeEndpointTests(TestCase):
	def setUp(self) -> None:
		self.client = Client()

	@patch("DSS_app.views.PyPDF2.PdfReader")
	@patch("DSS_app.views.extract_text_from_pdf_bytes")
	@patch("DSS_app.views.summarize_text")
	def test_api_returns_summary_and_flag(self, mock_summarize, mock_extract, mock_pdf_reader):
		mock_extract.return_value = "Hello world. " * 50
		mock_summarize.return_value = "Short summary"
		mock_pdf_reader.return_value.pages = [object()]

		# Uploaded bytes don't matter because we mock extraction, but a valid
		# multipart file must exist so request.FILES is populated.
		uploaded = SimpleUploadedFile(
			"test.pdf",
			b"%PDF-1.4\n% fake pdf bytes\n",
			content_type="application/pdf",
		)
		resp = self.client.post(
			"/api/summarize/",
			data={"file": uploaded},
		)

		self.assertEqual(resp.status_code, 200)
		payload = resp.json()
		self.assertTrue(payload.get("success"))
		self.assertEqual(payload.get("summary"), "Short summary")
		self.assertIn("summarization_used", payload)
