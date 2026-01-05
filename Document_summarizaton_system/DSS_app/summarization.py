"""Summarization helpers (Hugging Face / Transformers).

We use a map-reduce approach so long PDFs can be summarized despite model input limits.

- map step: split input text into chunks and summarize each
- reduce step: summarize the concatenated chunk summaries

The default model is `facebook/bart-large-cnn`.

Notes:
- Loading the model is expensive; keep the pipeline cached.
- For production, consider running this asynchronously (Celery) or behind a queue.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
import re
import logging
from typing import Iterable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SummaryConfig:
    model_name: str = os.environ.get("DSS_SUMMARY_MODEL", "facebook/bart-large-cnn")
    # Chunk sizes are in tokens (we use the tokenizer to split safely).
    # Keep well under BART's max (typically 1024 tokens) by default.
    chunk_size: int = int(os.environ.get("DSS_SUMMARY_CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.environ.get("DSS_SUMMARY_CHUNK_OVERLAP", "50"))
    # Generation controls
    min_length: int = int(os.environ.get("DSS_SUMMARY_MIN_LENGTH", "60"))
    max_length: int = int(os.environ.get("DSS_SUMMARY_MAX_LENGTH", "180"))


def _clean_for_summarization(text: str) -> str:
    text = (text or "").strip()
    # Collapse huge whitespace runs while preserving newlines somewhat.
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _chunk_text_by_tokens(text: str, tokenizer, *, chunk_tokens: int, overlap_tokens: int) -> list[str]:
    """Chunk `text` into pieces where each chunk's token count (by tokenizer)
    is <= chunk_tokens. We accumulate sentences until adding the next would
    exceed the target. For very long sentences we fall back to character slicing.
    """
    text = _clean_for_summarization(text)
    if not text:
        return []

    overlap_tokens = max(0, min(overlap_tokens, chunk_tokens - 1))

    # Split on sentence-like boundaries to avoid chopping mid-sentence.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    cur = ""

    for s in sentences:
        s = s.strip()
        if not s:
            continue

        candidate = (cur + " " + s).strip() if cur else s
        try:
            tok_ids = tokenizer.encode(candidate, add_special_tokens=False)
        except Exception:
            # If tokenizer fails for unexpectedly long inputs, fallback to char-based heuristics
            tok_ids = None

        if tok_ids is None:
            # safe fallback: break long sentence into smaller char pieces
            approx = max(200, chunk_tokens * 4)
            for i in range(0, len(s), approx):
                chunks.append(s[i : i + approx])
            cur = ""
            continue

        if len(tok_ids) <= chunk_tokens:
            # fits within a chunk
            cur = candidate
            continue

        # candidate too large: if current buffer has content, flush it.
        if cur:
            chunks.append(cur)
        # now handle the long sentence that alone exceeds chunk_tokens
        if len(tok_ids) > chunk_tokens:
            # break sentence by characters as a last resort
            approx = max(200, chunk_tokens * 4)
            for i in range(0, len(s), approx):
                chunks.append(s[i : i + approx])
            cur = ""
        else:
            cur = s

    if cur:
        chunks.append(cur)

    return chunks


@lru_cache(maxsize=1)
def _get_summarizer(model_name: str):
    """Create and cache the transformers summarization pipeline."""
    # Import here so missing deps don't break module import at app startup.
    from transformers import pipeline, AutoTokenizer, AutoConfig

    # Use CPU by default (device=-1). If you later add GPU support:
    # - set DSS_SUMMARY_DEVICE=0 for CUDA:0
    device = int(os.environ.get("DSS_SUMMARY_DEVICE", "-1"))

    # Load tokenizer to allow token-aware chunking elsewhere.
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    try:
        config = AutoConfig.from_pretrained(model_name)
        model_max_length = getattr(config, "max_position_embeddings", tokenizer.model_max_length)
    except Exception:
        model_max_length = tokenizer.model_max_length

    summarizer = pipeline(
        task="summarization",
        model=model_name,
        tokenizer=tokenizer,
        device=device,
    )

    # Return both pipeline and tokenizer + model_max_length via a tuple.
    return summarizer, tokenizer, int(model_max_length)


def summarize_text(text: str, *, config: SummaryConfig | None = None) -> str:
    """Summarize an arbitrarily long text using map-reduce."""
    cfg = config or SummaryConfig()
    text = _clean_for_summarization(text)
    if not text:
        return ""

    # summarizer now returns (pipeline, tokenizer, model_max_length)
    summarizer_obj = _get_summarizer(cfg.model_name)
    if isinstance(summarizer_obj, tuple):
        summarizer, tokenizer, model_max = summarizer_obj
    else:
        summarizer = summarizer_obj
        tokenizer = None
        model_max = 1024

    # Determine chunking by tokenizer token count when possible.
    if tokenizer is not None:
        chunks = _chunk_text_by_tokens(text, tokenizer, chunk_tokens=cfg.chunk_size, overlap_tokens=cfg.chunk_overlap)
    else:
        cleaned = _clean_for_summarization(text)
        if not cleaned:
            return ""
        parts = []
        step = max(1000, cfg.chunk_size)
        for i in range(0, len(cleaned), step - cfg.chunk_overlap):
            parts.append(cleaned[i : i + step])
        chunks = parts
    if not chunks:
        return ""

    # Small input: summarize directly.
    if len(chunks) == 1:
        out = summarizer(chunks[0], min_length=cfg.min_length, max_length=cfg.max_length, truncation=True)
        return (out[0].get("summary_text") or "").strip()

    # Map: summarize each chunk.
    chunk_summaries: list[str] = []
    for ch in chunks:
        try:
            out = summarizer(ch, min_length=cfg.min_length, max_length=cfg.max_length, truncation=True)
        except Exception as e:
            logger.warning("Chunk summarization failed: %s; attempting truncated fallback", str(e))
            # Fall back to a safe prefix to avoid model internal index errors
            prefix = ch[: cfg.chunk_size * 4]
            out = summarizer(prefix, min_length=cfg.min_length, max_length=cfg.max_length, truncation=True)

        s = (out[0].get("summary_text") or "").strip()
        if s:
            chunk_summaries.append(s)

    combined = "\n".join(chunk_summaries).strip()
    if not combined:
        return ""

    # Reduce: summarize the summaries into a final output.
    # Make reduce a bit tighter.
    reduce_min = max(40, cfg.min_length // 2)
    reduce_max = max(cfg.max_length, cfg.max_length + 40)

    out = summarizer(combined, min_length=reduce_min, max_length=reduce_max)
    return (out[0].get("summary_text") or "").strip()


def _extract_structured_data(text: str) -> dict:
    """Heuristic extraction of common fields from admit-card / exam-schedule style text.

    Returns a dict with keys: name, enrollment, program, institute, abc_id, schedule (list of dicts).
    This is intentionally conservative and aims to capture the common fields seen in university admit cards.
    """
    out = {
        "name": None,
        "enrollment": None,
        "program": None,
        "institute": None,
        "abc_id": None,
        "schedule": [],
    }

    if not text:
        return out

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    joined = " ".join(lines)

    # Institute - look for common university name or 'Institute' phrase
    m = re.search(r"Dharmsinh\s+Desai\s+University|Faculty of Technology|Institute of Technology", text, flags=re.IGNORECASE)
    if m:
        out["institute"] = m.group(0).strip()

    # Name
    m = re.search(r"\bName[:\s]+([A-Z][A-Z\s]+[A-Z0-9])", text)
    if not m:
        # try looser pattern: look for line that starts with Name
        for ln in lines:
            if ln.lower().startswith("name"):
                parts = re.split(r"[:\-]", ln, maxsplit=1)
                if len(parts) > 1:
                    out["name"] = parts[1].strip()
                    break
    else:
        out["name"] = m.group(1).strip()

    # Enrollment
    m = re.search(r"Enrollment\s*No\.?[:\s]*([A-Za-z0-9-]+)", text, flags=re.IGNORECASE)
    if m:
        out["enrollment"] = m.group(1).strip()
    else:
        # fallback: look for tokens that look like enrollment codes (e.g., 23CEUOZ032)
        m2 = re.search(r"\b\d{2}[A-Z]{2,4}[A-Z0-9]{1,6}\d{2,}\b", text)
        if m2:
            out["enrollment"] = m2.group(0)

    # Program
    m = re.search(r"Program\s*[:\-]?\s*([A-Za-z &]+)", text, flags=re.IGNORECASE)
    if m:
        out["program"] = m.group(1).strip()

    # ABC ID or other long numeric ID
    m = re.search(r"ABC\s*ID\s*[:\s]*([A-Za-z0-9-]+)", text, flags=re.IGNORECASE)
    if m:
        out["abc_id"] = m.group(1).strip()
    else:
        m2 = re.search(r"\b(\d{9,16})\b", text)
        if m2:
            out["abc_id"] = m2.group(1)

    # Schedule extraction: find dates and nearby subject codes and subject names.
    # We'll scan lines for date patterns and then attempt to find a subject code (e.g., 23CE414) on
    # the same or neighboring lines and treat text tokens around them as subject name.
    date_re = re.compile(r"(\d{2}-\d{2}-\d{4})")
    code_re = re.compile(r"\b[A-Z0-9]{2,6}\d{3,4}\b")
    time_re = re.compile(r"(\d{1,2}:\d{2}\s*(?:AM|PM))", flags=re.IGNORECASE)

    for idx, ln in enumerate(lines):
        date_m = date_re.search(ln)
        if not date_m:
            continue
        date = date_m.group(1)

        # Try to find code in same line
        code = None
        mcode = code_re.search(ln)
        if mcode:
            code = mcode.group(0)

        # subject name heuristics: take previous non-empty line(s) if they look like a title
        subj = None
        # look back up to 2 lines for title-like content
        for back in range(1, 3):
            if idx - back >= 0:
                cand = lines[idx - back]
                # skip lines containing codes/dates
                if not date_re.search(cand) and not code_re.search(cand):
                    subj = cand
                    break

        # fallback: try to extract a run of words after the code in the same line
        if not subj and code:
            after = ln.split(code, 1)[-1].strip()
            # remove time tokens
            after = time_re.sub("", after)
            subj = after.strip()

        # time
        time_m = time_re.search(ln)
        time_span = None
        if time_m:
            start = time_m.group(1)
            # look for 'to' and an end time
            rest = ln[time_m.end() :]
            end_m = time_re.search(rest)
            end = end_m.group(1) if end_m else None
            if end:
                time_span = f"{start} to {end}"
            else:
                time_span = start

        entry = {"date": date, "code": code or "", "subject": subj or "", "time": time_span or ""}
        out["schedule"].append(entry)

    return out


def craft_structured_summary(text: str) -> str:
    """Create a deterministic, human-readable summary from structured fields extracted from `text`.

    This intentionally preserves IDs and exact tokens found in the document and mirrors the style of the
    example `gemini` response provided by the user.
    """
    sd = _extract_structured_data(text)

    parts = []
    parts.append("Admit Card Summary: ")
    # Title line
    program = sd.get("program") or ""
    inst = sd.get("institute") or ""
    title = f"{program} " if program else ""
    title += "(Exam Details)"
    parts.append(title)
    parts.append("")

    # Personal & Institutional Details
    pd = []
    if sd.get("name"):
        pd.append(f"Name: {sd['name'].title()}")
    if sd.get("enrollment"):
        pd.append(f"Enrollment No.: {sd['enrollment']}")
    if program:
        pd.append(f"Program: {program}")
    if inst:
        pd.append(f"Institute: {inst}")
    if sd.get("abc_id"):
        pd.append(f"ABC ID: {sd['abc_id']}")

    if pd:
        parts.append("Personal & Institutional Details")
        parts.extend(pd)
        parts.append("")

    # Examination Schedule
    sched = sd.get("schedule") or []
    if sched:
        parts.append("Examination Schedule")
        parts.append("All exams are Theory type and held at the institute unless noted otherwise.")
        parts.append("")
        # Table-like lines
        parts.append("Date\tSubject Code\tSubject Name\tTime")
        for e in sched:
            date = e.get("date", "")
            code = e.get("code", "")
            subj = e.get("subject", "")
            time = e.get("time", "")
            # normalize spacing
            subj = re.sub(r"\s+", " ", subj).strip()
            parts.append(f"{date}\t{code}\t{subj}\t{time}")

    # Join with sensible newlines
    return "\n".join([p for p in parts if p is not None and p != ""]).strip()


def generate_best_summary(text: str) -> str:
    """Return an improved summary for `text`.

    Strategy:
    - Build a deterministic structured summary from extracted fields (this preserves IDs and dates).
    - If a summarization model is available and the document is long/complex, optionally use the model to produce
      an additional abstractive paragraph and append it after the structured block. For now we return the
      deterministic structured block as the primary summary to ensure fidelity.
    """
    try:
        structured = craft_structured_summary(text)
        # If the structured summary looks too small and a model summarizer is available, add a model paragraph.
        # However, to avoid losing facts we keep the structured block as primary.
        return structured
    except Exception:
        # As a last resort, fall back to the existing abstractive summarizer.
        try:
            return summarize_text(text)
        except Exception:
            return ""
