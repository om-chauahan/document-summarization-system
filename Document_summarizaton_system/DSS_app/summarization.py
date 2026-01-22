"""Summarization helpers (Local LLM via Ollama).

All Hugging Face / BART / transformers-based summarization has been removed.

This uses a local LLM through Ollama. Example setup:
- Install Ollama: https://ollama.com
- Pull a model once: `ollama pull mistral`
- Ensure Ollama is running (default: http://localhost:11434)

We send extracted text with a prompt that requests clean section headings and
dash-bullets for key details (no markdown).
"""

from __future__ import annotations

import hashlib
import logging
import os
import re

logger = logging.getLogger(__name__)


DEFAULT_OLLAMA_MODEL = os.environ.get("DSS_OLLAMA_MODEL", "mistral")
DEFAULT_OLLAMA_HOST = os.environ.get("DSS_OLLAMA_HOST", "http://localhost:11434")


# Simple in-process cache to avoid recomputing the same summary repeatedly.
# Note: in multi-process deployments, each process has its own cache.
_SUMMARY_CACHE: dict[str, str] = {}
_SUMMARY_CACHE_ORDER: list[str] = []
_SUMMARY_CACHE_MAX_ITEMS = int(os.environ.get("DSS_SUMMARY_CACHE_MAX_ITEMS", "24"))


def _cache_get(key: str) -> str | None:
    return _SUMMARY_CACHE.get(key)


def _cache_set(key: str, value: str) -> None:
    if _SUMMARY_CACHE_MAX_ITEMS <= 0:
        return
    if key in _SUMMARY_CACHE:
        _SUMMARY_CACHE[key] = value
        return
    _SUMMARY_CACHE[key] = value
    _SUMMARY_CACHE_ORDER.append(key)
    while len(_SUMMARY_CACHE_ORDER) > _SUMMARY_CACHE_MAX_ITEMS:
        old = _SUMMARY_CACHE_ORDER.pop(0)
        _SUMMARY_CACHE.pop(old, None)


def _compress_for_llm(text: str, *, max_chars: int) -> str:
    """Reduce input size cheaply to keep Ollama fast.

    This is intentionally simple (no extra deps):
    - keep headings + bullet lines
    - keep the first chunk
    - keep a small tail chunk (often contains conclusions)
    - include some lines that contain numbers/emails/ids

    This prevents huge PDFs from forcing the model to process too many tokens.
    """

    src = (text or "").strip()
    if not src:
        return ""

    lines = [ln.strip() for ln in src.splitlines() if ln.strip()]
    if not lines:
        return src[:max_chars]

    # 1) Remove repeated header/footer lines (very common in PDF extraction)
    # We only consider relatively short lines that repeat many times.
    counts: dict[str, int] = {}
    for ln in lines:
        key = ln
        if 5 <= len(key) <= 80:
            counts[key] = counts.get(key, 0) + 1

    # If a short line repeats on many lines, it's likely a header/footer.
    repeat_threshold = max(4, len(lines) // 8)
    repeated = {ln for ln, c in counts.items() if c >= repeat_threshold}

    def is_noise(ln: str) -> bool:
        if ln in repeated:
            return True
        # Page markers and boilerplate noise
        if re.match(r"^page\s*\d+(\s*of\s*\d+)?$", ln, re.I):
            return True
        if re.match(r"^\d+\s*/\s*\d+$", ln):
            return True
        if re.match(r"^(confidential|copyright|all rights reserved)\b", ln, re.I):
            return True
        # Extremely long 'separator' lines
        if re.fullmatch(r"[-_=]{10,}", ln):
            return True
        return False

    filtered = [ln for ln in lines if not is_noise(ln)]
    if filtered:
        lines = filtered

    # If the cleaned text is already within budget, return it (still benefits from noise removal).
    cleaned = "\n".join(lines).strip()
    if len(cleaned) <= max_chars:
        return cleaned

    def looks_important(ln: str) -> bool:
        # General heuristics to identify information-rich lines (works for any document type)
        # Lines with structured formatting (bullets, numbered lists)
        if re.match(r"^([\-•\*]|\d+[\.)])\s+", ln):
            return True
        # Short all-caps lines (often headings or labels)
        if len(ln) <= 90 and ln.isupper():
            return True
        # Lines containing structured data patterns
        if re.search(r"\b(\+?\d[\d\s().-]{7,}\d)\b", ln):  # Phone numbers
            return True
        if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", ln):  # Email addresses
            return True
        # Lines with multiple numbers (likely contain data/identifiers)
        if len(re.findall(r"\b\d{2,}\b", ln)) >= 2:
            return True
        # Lines with common data identifiers (general patterns, not specific to one domain)
        if re.search(r"\b([A-Z]{2,}\d+|\d+[A-Z]{2,}|[A-Z]+\s*\d+|\d+\s*[A-Z]+)\b", ln):  # Alphanumeric codes
            return True
        # Lines with date/time patterns
        if re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}:\d{2})\b", ln):
            return True
        return False

    head_budget = int(max_chars * 0.60)
    tail_budget = int(max_chars * 0.25)
    mid_budget = max_chars - head_budget - tail_budget

    joined = "\n".join(lines)
    head_txt = joined[:head_budget]
    tail_txt = joined[-tail_budget:]

    important_lines: list[str] = []
    for ln in lines:
        if looks_important(ln):
            important_lines.append(ln)
        if sum(len(x) + 1 for x in important_lines) >= mid_budget:
            break

    mid_txt = "\n".join(important_lines)

    combined = (head_txt + "\n\n---\n\n" + mid_txt + "\n\n---\n\n" + tail_txt).strip()
    return combined[:max_chars]


def summarize_text(
    text: str,
    *,
    prompt: str | None = None,
    model: str | None = None,
) -> str:
    """Summarize text using a local Ollama model.

    Output is fully model-generated.
    """

    src = (text or "").strip()
    if not src:
        return ""

    model_name = (model or DEFAULT_OLLAMA_MODEL).strip() or "mistral"
    # General, efficient prompt that works for any document type without manual cases
    system_prompt = (
        prompt
        or "You are an expert document analyst. Create a comprehensive, accurate summary that captures all essential information from the provided content.\n\n"
        "Core principles:\n"
        "- Extract and preserve all factual information exactly as it appears (names, numbers, dates, codes, identifiers, contact details)\n"
        "- Maintain accuracy: only include information that is explicitly stated in the source\n"
        "- Be thorough: include all significant details, not just high-level points\n"
        "- Use clear, direct language without vague references or meta-commentary\n\n"
        "Output format:\n"
        "- Use descriptive section headings on separate lines\n"
        "- Under each section, use bullet points (starting with '-') for individual facts\n"
        "- Organize information logically based on the document's structure and content\n"
        "- Do not use markdown formatting (no **, #, or backticks)\n"
        "- Write directly about the content, not about the document itself\n\n"
        "Quality standards:\n"
        "- Every important detail from the source should appear in the summary\n"
        "- Preserve exact values, identifiers, and specific information\n"
        "- Group related information under appropriate headings\n"
        "- Ensure the summary is self-contained and informative"
    )

    # Bound input size to keep latency predictable.
    # For speed without losing key details, we rely on smarter compression rather than harsh truncation.
    max_chars = int(os.environ.get("DSS_OLLAMA_MAX_CHARS", "10500"))
    src = _compress_for_llm(src, max_chars=max_chars)

    # Cache: same input + settings => instant response.
    num_predict = int(os.environ.get("DSS_OLLAMA_NUM_PREDICT", "330"))
    num_ctx = int(os.environ.get("DSS_OLLAMA_NUM_CTX", "1024"))
    temperature = float(os.environ.get("DSS_OLLAMA_TEMPERATURE", "0.2"))
    top_p = float(os.environ.get("DSS_OLLAMA_TOP_P", "0.9"))
    src_hash = hashlib.sha256(src.encode("utf-8", errors="ignore")).hexdigest()
    cache_key = f"v1|{model_name}|{max_chars}|{num_ctx}|{num_predict}|{temperature}|{top_p}|{src_hash}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # Lazy import so server can start even if dependency is missing.
    try:
        import ollama  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Missing dependency 'ollama'. Install it with: pip install ollama") from e

    # Configure host (supported by the ollama python client).
    os.environ.setdefault("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)

    try:
        resp = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": src},
            ],
            options={
                "temperature": temperature,
                # Keep generations short for speed; override via env.
                "num_predict": num_predict,
                # Smaller context window reduces work for long PDFs.
                "num_ctx": num_ctx,
                "top_p": top_p,
            },
        )
    except Exception as e:
        logger.error("Ollama summarization failed: %s", str(e), exc_info=True)
        raise RuntimeError(f"Ollama summarization failed: {str(e)}") from e

    content = ((resp or {}).get("message") or {}).get("content")
    out = (content or "").strip()
    if out:
        _cache_set(cache_key, out)
    return out


def stream_summary(
    text: str,
    *,
    prompt: str | None = None,
    model: str | None = None,
):
    """Yield summary text chunks as they are generated by Ollama.

    This is used by the streaming API endpoint to avoid UI lag and to show
    progress immediately.
    """

    src = (text or "").strip()
    if not src:
        return

    model_name = (model or DEFAULT_OLLAMA_MODEL).strip() or "mistral"
    # General, efficient prompt that works for any document type without manual cases
    system_prompt = (
        prompt
        or "You are an expert document analyst. Create a comprehensive, accurate summary that captures all essential information from the provided content.\n\n"
        "Core principles:\n"
        "- Extract and preserve all factual information exactly as it appears (names, numbers, dates, codes, identifiers, contact details)\n"
        "- Maintain accuracy: only include information that is explicitly stated in the source\n"
        "- Be thorough: include all significant details, not just high-level points\n"
        "- Use clear, direct language without vague references or meta-commentary\n\n"
        "Output format:\n"
        "- Use descriptive section headings on separate lines\n"
        "- Under each section, use bullet points (starting with '-') for individual facts\n"
        "- Organize information logically based on the document's structure and content\n"
        "- Do not use markdown formatting (no **, #, or backticks)\n"
        "- Write directly about the content, not about the document itself\n\n"
        "Quality standards:\n"
        "- Every important detail from the source should appear in the summary\n"
        "- Preserve exact values, identifiers, and specific information\n"
        "- Group related information under appropriate headings\n"
        "- Ensure the summary is self-contained and informative"
    )

    max_chars = int(os.environ.get("DSS_OLLAMA_MAX_CHARS", "7500"))
    src = _compress_for_llm(src, max_chars=max_chars)

    try:
        import ollama  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Missing dependency 'ollama'. Install it with: pip install ollama") from e

    os.environ.setdefault("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)

    try:
        # stream=True makes the client yield incremental chunks.
        for part in ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": src},
            ],
            options={
                "temperature": float(os.environ.get("DSS_OLLAMA_TEMPERATURE", "0.2")),
                "num_predict": int(os.environ.get("DSS_OLLAMA_NUM_PREDICT", "330")),
                "num_ctx": int(os.environ.get("DSS_OLLAMA_NUM_CTX", "1024")),
                "top_p": float(os.environ.get("DSS_OLLAMA_TOP_P", "0.9")),
            },
            stream=True,
        ):
            content = ((part or {}).get("message") or {}).get("content")
            if content:
                yield content
    except Exception as e:
        logger.error("Ollama streaming failed: %s", str(e), exc_info=True)
        raise RuntimeError(f"Ollama streaming failed: {str(e)}") from e
