from __future__ import annotations

from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch


class SummarizationHelpersTests(TestCase):
	def test_summarize_text_empty_input(self):
		from DSS_app.summarization import summarize_text
		self.assertEqual(summarize_text(""), "")

	def test_default_prompt_bans_vague_phrases(self):
		"""Regression: prevent summaries like 'name is mentioned' instead of real values."""
		from DSS_app import summarization as s
		# The prompt is a local variable inside summarize_text; validate via source.
		# If prompt wording changes, keep these bans in place.
		src = s.summarize_text.__code__.co_consts
		joined = " ".join([c for c in src if isinstance(c, str)])
		self.assertIn("BANNED vague phrases", joined)
		self.assertIn("is mentioned", joined)
		self.assertIn("Not found", joined)

	def test_compress_removes_repeated_headers_preserves_key_lines(self):
		from DSS_app.summarization import _compress_for_llm
		text = "\n".join(
			[
				"ACME AIRLINES - ITINERARY",
				"Page 1 of 3",
				"Passenger: John Doe",
				"PNR: XY12ZZ",
				"Flight: AC123  10 Jan 2026  10:30",
				"ACME AIRLINES - ITINERARY",
				"Page 2 of 3",
				"Seat: 12A",
				"Gate: B7",
				"ACME AIRLINES - ITINERARY",
				"Page 3 of 3",
			]
		)
		out = _compress_for_llm(text, max_chars=200)
		# Repeated header should be removed (ideally entirely).
		self.assertNotIn("ACME AIRLINES - ITINERARY\nACME AIRLINES - ITINERARY", out)
		# Page markers should be dropped.
		self.assertNotIn("Page 1 of 3", out)
		# Key details should still survive compression.
		self.assertIn("PNR: XY12ZZ", out)
		self.assertTrue(("Seat: 12A" in out) or ("Flight: AC123" in out))


class SummarizeEndpointTests(TestCase):
	def setUp(self) -> None:
		self.client = Client()

	@patch("DSS_app.views.PyPDF2.PdfReader")
	@patch("DSS_app.views.extract_text_from_pdf_bytes")
	@patch("DSS_app.views.model_summarize_text")
	def test_api_returns_summary_and_flag(self, mock_model_sum, mock_extract, mock_pdf_reader):
		mock_extract.return_value = "Hello world. " * 50
		mock_model_sum.return_value = "Short summary"
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
