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
import threading
from contextlib import contextmanager
import platform

logger = logging.getLogger(__name__)


DEFAULT_OLLAMA_MODEL = os.environ.get("DSS_OLLAMA_MODEL", "mistral")
DEFAULT_OLLAMA_HOST = os.environ.get("DSS_OLLAMA_HOST", "http://localhost:11434")


# Simple in-process cache to avoid recomputing the same summary repeatedly.
# Note: in multi-process deployments, each process has its own cache.
_SUMMARY_CACHE: dict[str, str] = {}
_SUMMARY_CACHE_ORDER: list[str] = []
_SUMMARY_CACHE_MAX_ITEMS = int(os.environ.get("DSS_SUMMARY_CACHE_MAX_ITEMS", "24"))


def _default_num_threads() -> int:
    """Pick a conservative default so Ollama doesn't peg the CPU.

    Leaving a couple cores free keeps the UI responsive on laptops.
    """

    # Conservative defaults to keep laptops responsive.
    try:
        cpu = os.cpu_count() or 4
    except Exception:
        cpu = 4

    sysname = (platform.system() or "").lower()
    # macOS laptops tend to feel worse when all performance cores are pegged.
    if sysname == "darwin":
        return max(1, min(4, cpu // 2))
    return max(1, min(6, cpu // 2))


_MAX_CONCURRENCY = int(os.environ.get("DSS_OLLAMA_MAX_CONCURRENCY", "1"))
_OLLAMA_SEM = threading.Semaphore(max(1, _MAX_CONCURRENCY))


@contextmanager
def _ollama_slot():
    """Limit concurrent Ollama generations to avoid system thrash."""

    _OLLAMA_SEM.acquire()
    try:
        yield
    finally:
        try:
            _OLLAMA_SEM.release()
        except Exception:
            # ignore
            pass


def _postprocess_to_n_lines(text: str, *, target_lines: int = 20) -> str:
    """Force output into exactly `target_lines` bullet lines without omitting content.

    Strategy:
    - Normalize to bullet lines.
    - If too few lines, split long lines into multiple factual lines.
    - If too many lines, merge extra lines into previous lines (preserves content).

    This is a formatting step; it does not add new facts.
    """

    raw = (text or "").replace("\r", "").strip()
    if not raw:
        return ""

    # Start with existing lines; if model returned paragraphs, these might be long.
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    if not lines:
        return ""

    def strip_bullet_prefix(ln: str) -> str:
        ln = ln.strip()
        # Normalize numbered items and various bullets.
        ln = re.sub(r"^\d+[.)]\s+", "", ln)
        ln = re.sub(r"^[-•*]\s+", "", ln)
        return ln.strip()

    def as_bullet(ln: str) -> str:
        core = strip_bullet_prefix(ln)
        return f"- {core}" if core else ""

    # Normalize initial bullets.
    norm = [as_bullet(ln) for ln in lines]
    norm = [ln for ln in norm if ln]

    # If too few lines, split long bullets by common separators.
    split_seps = ["; ", " | ", " • ", ". ", ", "]

    def split_one(bullet_line: str) -> list[str]:
        core = strip_bullet_prefix(bullet_line)
        if len(core) < 140:
            return [as_bullet(core)]

        for sep in split_seps:
            if sep in core:
                parts = [p.strip() for p in core.split(sep) if p.strip()]
                # Avoid creating too many tiny fragments.
                if len(parts) >= 2:
                    out = []
                    buf = ""
                    for p in parts:
                        if not buf:
                            buf = p
                            continue
                        # Merge very small fragments into the buffer.
                        if len(p) < 25 or len(buf) < 25:
                            buf = f"{buf}{sep.strip()} {p}".strip()
                        else:
                            out.append(buf)
                            buf = p
                    if buf:
                        out.append(buf)
                    return [as_bullet(x) for x in out if x.strip()]

        # Fallback: hard wrap by length at whitespace.
        words = core.split()
        out = []
        buf = ""
        for w in words:
            if not buf:
                buf = w
                continue
            if len(buf) + 1 + len(w) <= 120:
                buf = f"{buf} {w}"
            else:
                out.append(buf)
                buf = w
        if buf:
            out.append(buf)
        return [as_bullet(x) for x in out if x.strip()]

    i = 0
    while len(norm) < target_lines and i < len(norm):
        ln = norm[i]
        core = strip_bullet_prefix(ln)
        if len(core) >= 140:
            parts = split_one(ln)
            if len(parts) > 1:
                norm = norm[:i] + parts + norm[i + 1 :]
                continue
        i += 1

    # If still too few lines, split the longest line until we reach target.
    safety = 0
    while len(norm) < target_lines and safety < 60:
        safety += 1
        # pick longest
        idx = max(range(len(norm)), key=lambda k: len(strip_bullet_prefix(norm[k])))
        parts = split_one(norm[idx])
        if len(parts) <= 1:
            break
        norm = norm[:idx] + parts + norm[idx + 1 :]

    # If too many lines, merge extras into previous lines (preserves content).
    while len(norm) > target_lines:
        extra = strip_bullet_prefix(norm.pop())
        if not extra:
            continue
        prev = strip_bullet_prefix(norm[-1]) if norm else ""
        merged = (prev + "; " + extra).strip("; ")
        norm[-1] = as_bullet(merged)

    # Final pass: ensure bullets and non-empty, and exact length.
    norm = [as_bullet(ln) for ln in norm]
    norm = [ln for ln in norm if strip_bullet_prefix(ln)]
    if len(norm) > target_lines:
        norm = norm[:target_lines]
    return "\n".join(norm)


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
    - remove common repeated header/footer noise from PDFs
    - keep information-rich lines (headings, bullets, ids, dates, numbers)
    - ensure coverage across the FULL document (start/middle/end)

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
        # Common heading/section patterns
        if re.match(r"^(section|chapter|unit|module)\b", ln, re.I):
            return True
        if re.match(r"^\d+(?:\.\d+)*\s+\S+", ln):
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

    def take_prefix_by_chars(seq: list[str], budget: int) -> str:
        out: list[str] = []
        used = 0
        for ln in seq:
            need = len(ln) + 1
            if out and used + need > budget:
                break
            if not out and need > budget:
                out.append(ln[: max(0, budget)])
                break
            out.append(ln)
            used += need
        return "\n".join(out).strip()

    def take_suffix_by_chars(seq: list[str], budget: int) -> str:
        out: list[str] = []
        used = 0
        for ln in reversed(seq):
            need = len(ln) + 1
            if out and used + need > budget:
                break
            if not out and need > budget:
                out.append(ln[-max(0, budget) :])
                break
            out.append(ln)
            used += need
        return "\n".join(reversed(out)).strip()

    # Budget split. We intentionally put the HEAD and the cross-document IMPORTANT
    # lines at the *end* of the prompt, because when input exceeds `num_ctx`, many
    # runtimes keep the LAST tokens (which otherwise biases summaries toward the
    # document's ending).
    head_budget = int(max_chars * 0.22)
    tail_budget = int(max_chars * 0.18)
    mid_budget = max_chars - head_budget - tail_budget

    head_txt = take_prefix_by_chars(lines, head_budget)
    tail_txt = take_suffix_by_chars(lines, tail_budget)

    # Collect candidate lines across the entire document.
    candidates: list[tuple[int, str]] = [
        (i, ln) for i, ln in enumerate(lines) if looks_important(ln)
    ]

    # Ensure coverage even for "plain paragraph" docs.
    if len(candidates) < 12:
        step = max(1, len(lines) // 60)
        for i in range(0, len(lines), step):
            candidates.append((i, lines[i]))

    # De-dupe by index while preserving order.
    seen_idx: set[int] = set()
    candidates_sorted = []
    for i, ln in sorted(candidates, key=lambda t: t[0]):
        if i in seen_idx:
            continue
        seen_idx.add(i)
        candidates_sorted.append((i, ln))

    # Evenly sample candidates across the doc into the mid budget.
    if candidates_sorted:
        # Start with an even stride; adjust if we still exceed budget.
        stride = max(1, len(candidates_sorted) // 120)
        sampled = [ln for _, ln in candidates_sorted[::stride]]
    else:
        sampled = []

    # Trim sampled lines to fit mid budget.
    mid_lines: list[str] = []
    used = 0
    for ln in sampled:
        need = len(ln) + 1
        if mid_lines and used + need > mid_budget:
            break
        if not mid_lines and need > mid_budget:
            mid_lines.append(ln[: max(0, mid_budget)])
            used = mid_budget
            break
        mid_lines.append(ln)
        used += need

    mid_txt = "\n".join(mid_lines).strip()

    sep = "\n\n---\n\n"
    # Put tail first, then cross-document mid sample, then head last.
    # If upstream truncates from the front, the head/mid content survives.
    combined = (tail_txt + sep + mid_txt + sep + head_txt).strip()
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
    # Prompt tuned for: (a) exactly 20 lines, (b) broad coverage across the whole text.
    system_prompt = (
        prompt
        or "give summary of given text without missing anything . and summary length is 20 lines .\n"
        "Rules (follow strictly):\n"
        "- Output EXACTLY 20 non-empty lines.\n"
        "- Each line must contain at least one concrete fact from the text (names, numbers, dates, times, codes/IDs, key terms).\n"
        "- COVER THE ENTIRE DOCUMENT: include points from the beginning, middle, and end; do not focus only on the last part.\n"
        "- Do not skip any major section/topic; if there are too many details, MERGE related facts into one line instead of omitting a section.\n"
        "- No filler/meta phrases like: 'not specified', 'not provided', 'unknown', 'N/A', 'is mentioned'.\n"
        "- Plain text only; one bullet ('- ') per line; no markdown headings."
    )

    # Bound input size to keep latency predictable.
    # For speed without losing key details, we rely on smarter compression rather than harsh truncation.
    # Default tuned for smoother local runs (esp. 8GB RAM). Override via env.
    max_chars = int(os.environ.get("DSS_OLLAMA_MAX_CHARS", "4500"))
    src = _compress_for_llm(src, max_chars=max_chars)

    # Cache: same input + settings => instant response.
    # Must be high enough to finish 20 factual lines; too-low values truncate mid-output.
    num_predict = int(os.environ.get("DSS_OLLAMA_NUM_PREDICT", "480"))
    # Slightly larger context helps accuracy; override down if your machine struggles.
    num_ctx = int(os.environ.get("DSS_OLLAMA_NUM_CTX", "2048"))
    temperature = float(os.environ.get("DSS_OLLAMA_TEMPERATURE", "0.2"))
    top_p = float(os.environ.get("DSS_OLLAMA_TOP_P", "0.9"))
    num_thread = int(os.environ.get("DSS_OLLAMA_NUM_THREAD", str(_default_num_threads())))
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
        with _ollama_slot():
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
                    # Larger context window helps avoid dropping early content.
                    "num_ctx": num_ctx,
                    "top_p": top_p,
                    # Limit CPU usage for responsiveness.
                    "num_thread": max(1, num_thread),
                },
            )
    except Exception as e:
        logger.error("Ollama summarization failed: %s", str(e), exc_info=True)
        raise RuntimeError(f"Ollama summarization failed: {str(e)}") from e

    content = ((resp or {}).get("message") or {}).get("content")
    out = (content or "").strip()
    out = _postprocess_to_n_lines(out, target_lines=20)
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
    system_prompt = (
        prompt
        or "give summary of given text without missing anything . and summary length is 20 lines .\n"
        "Rules (follow strictly):\n"
        "- Output EXACTLY 20 non-empty lines.\n"
        "- Each line must contain at least one concrete fact from the text (names, numbers, dates, times, codes/IDs, key terms).\n"
        "- COVER THE ENTIRE DOCUMENT: include points from the beginning, middle, and end; do not focus only on the last part.\n"
        "- Do not skip any major section/topic; if there are too many details, MERGE related facts into one line instead of omitting a section.\n"
        "- No filler/meta phrases like: 'not specified', 'not provided', 'unknown', 'N/A', 'is mentioned'.\n"
        "- Plain text only; one bullet ('- ') per line; no markdown headings."
    )

    max_chars = int(os.environ.get("DSS_OLLAMA_MAX_CHARS", "4500"))
    src = _compress_for_llm(src, max_chars=max_chars)

    try:
        import ollama  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Missing dependency 'ollama'. Install it with: pip install ollama") from e

    os.environ.setdefault("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)

    try:
        num_thread = int(os.environ.get("DSS_OLLAMA_NUM_THREAD", str(_default_num_threads())))
        options = {
            "temperature": float(os.environ.get("DSS_OLLAMA_TEMPERATURE", "0.2")),
            "num_predict": int(os.environ.get("DSS_OLLAMA_NUM_PREDICT", "480")),
            "num_ctx": int(os.environ.get("DSS_OLLAMA_NUM_CTX", "2048")),
            "top_p": float(os.environ.get("DSS_OLLAMA_TOP_P", "0.9")),
            "num_thread": max(1, num_thread),
        }

        with _ollama_slot():
            # stream=True makes the client yield incremental chunks.
            for part in ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": src},
                ],
                options=options,
                stream=True,
            ):
                content = ((part or {}).get("message") or {}).get("content")
                if content:
                    yield content
    except Exception as e:
        logger.error("Ollama streaming failed: %s", str(e), exc_info=True)
        raise RuntimeError(f"Ollama streaming failed: {str(e)}") from e
