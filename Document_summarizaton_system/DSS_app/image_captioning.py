from __future__ import annotations

import logging
import os
import threading
import io

logger = logging.getLogger(__name__)

# Use a lightweight model for faster processing
_DEFAULT_BLIP_MODEL = os.environ.get(
    "DSS_BLIP_MODEL", "Salesforce/blip-image-captioning-base"
)

# Thread-safe model caching - load once, use many times
_BLIP_LOCK = threading.Lock()
_BLIP_PROCESSOR = None
_BLIP_MODEL = None
_BLIP_DEVICE = None
_BLIP_LOADED = False


def _format_caption_as_summary(caption: str) -> str:
    """Format a simple caption into structured summary format (fast, no LLM needed).
    
    Converts a caption like "A group of people standing on top of a building" into:
    
    Scene Description
    - A group of people standing on top of a building
    - [Additional details based on caption]
    
    This is much faster than using Ollama.
    """
    if not caption:
        return ""
    
    caption = caption.strip()
    
    # Extract key elements from caption
    words = caption.lower().split()
    
    # Identify main subject and activity
    people_keywords = ['people', 'person', 'men', 'women', 'children', 'group', 'crowd', 'individuals']
    activity_keywords = ['standing', 'sitting', 'walking', 'running', 'playing', 'working', 'talking', 'looking']
    location_keywords = ['building', 'room', 'street', 'park', 'beach', 'mountain', 'field', 'indoor', 'outdoor']
    object_keywords = ['car', 'table', 'chair', 'tree', 'water', 'sky', 'ground', 'wall', 'door', 'window']
    
    has_people = any(kw in caption.lower() for kw in people_keywords)
    has_activity = any(kw in caption.lower() for kw in activity_keywords)
    has_location = any(kw in caption.lower() for kw in location_keywords)
    has_objects = any(kw in caption.lower() for kw in object_keywords)
    
    # Build structured summary
    sections = []
    
    # Main Scene Description
    sections.append("Scene Description")
    sections.append(f"- {caption}")
    
    # Add People section if relevant
    if has_people:
        sections.append("\nPeople")
        if 'group' in caption.lower() or 'people' in caption.lower():
            sections.append("- Multiple people visible in the scene")
        if 'person' in caption.lower():
            sections.append("- Individual person present")
        if has_activity:
            sections.append("- People engaged in visible activity")
    
    # Add Activity section if relevant
    if has_activity:
        sections.append("\nActivity")
        for act in activity_keywords:
            if act in caption.lower():
                sections.append(f"- People are {act}")
                break
    
    # Add Setting section if relevant
    if has_location:
        sections.append("\nSetting")
        for loc in location_keywords:
            if loc in caption.lower():
                sections.append(f"- Location appears to be {loc} or related area")
                break
        if 'outdoor' in caption.lower() or 'outside' in caption.lower():
            sections.append("- Outdoor environment")
        elif 'indoor' in caption.lower() or 'inside' in caption.lower():
            sections.append("- Indoor environment")
    
    # Add Objects section if relevant
    if has_objects:
        sections.append("\nObjects and Elements")
        for obj in object_keywords:
            if obj in caption.lower():
                sections.append(f"- {obj.capitalize()} visible in the scene")
    
    # Add General Observations
    sections.append("\nGeneral Observations")
    if len(caption.split()) > 5:
        sections.append("- Detailed scene with multiple elements")
    sections.append("- Image contains observable visual information")
    
    return "\n".join(sections)


def _get_device(torch):
    """Detect the best available device (MPS for Mac, CUDA for GPU, CPU otherwise)."""
    try:
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    try:
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _load_blip():
    """Lazy-load BLIP processor/model once per process (thread-safe).
    
    The model is loaded only once and cached in memory for fast subsequent use.
    """
    global _BLIP_PROCESSOR, _BLIP_MODEL, _BLIP_DEVICE, _BLIP_LOADED

    # Fast path: if already loaded, return immediately
    if _BLIP_LOADED and _BLIP_PROCESSOR is not None and _BLIP_MODEL is not None:
        return _BLIP_PROCESSOR, _BLIP_MODEL, _BLIP_DEVICE

    # Thread-safe loading
    with _BLIP_LOCK:
        # Double-check after acquiring lock
        if _BLIP_LOADED and _BLIP_PROCESSOR is not None and _BLIP_MODEL is not None:
            return _BLIP_PROCESSOR, _BLIP_MODEL, _BLIP_DEVICE

        try:
            import torch  # type: ignore
            from transformers import BlipForConditionalGeneration, BlipProcessor  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "Image captioning requires torch and transformers. Install with: pip install torch transformers"
            ) from e

        device = _get_device(torch)
        model_name = (_DEFAULT_BLIP_MODEL or "").strip() or "Salesforce/blip-image-captioning-base"

        logger.info("Loading BLIP image captioning model '%s' on device=%s (one-time download)", model_name, device)

        try:
            # Load processor and model (will download on first use)
            processor = BlipProcessor.from_pretrained(model_name)
            model = BlipForConditionalGeneration.from_pretrained(model_name)
            model.to(device)
            model.eval()  # Set to evaluation mode for faster inference

            _BLIP_PROCESSOR = processor
            _BLIP_MODEL = model
            _BLIP_DEVICE = device
            _BLIP_LOADED = True

            logger.info("BLIP model loaded successfully and cached in memory")
            return processor, model, device
        except Exception as e:
            logger.error("Failed to load BLIP model: %s", str(e), exc_info=True)
            raise RuntimeError(f"Failed to load image captioning model: {str(e)}") from e


def describe_image_bytes(
    image_bytes: bytes,
    *,
    max_new_tokens: int | None = None,
) -> str:
    """Generate a structured, detailed description for an image in the same format as document summaries.
    
    This function is optimized for speed:
    1. Gets initial caption from BLIP model (fast, cached)
    2. Formats it directly into structured format with sections and bullet points (instant)
    3. Matches the format used for document summaries without using Ollama
    
    Args:
        image_bytes: Raw image bytes (PNG, JPG, JPEG)
        max_new_tokens: Maximum tokens for initial caption (default: 80 for more detail)
    
    Returns:
        A structured description with sections and bullet points, matching document summary format.
    """
    if not image_bytes:
        return ""

    try:
        from PIL import Image  # pillow
    except ImportError as e:
        raise RuntimeError("Image processing requires pillow. Install with: pip install pillow") from e

    # Load BLIP model (cached after first call)
    try:
        processor, model, device = _load_blip()
    except Exception as e:
        logger.error("Cannot load image captioning model: %s", str(e))
        return ""

    # Decode image
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        logger.exception("Failed to decode image bytes for captioning")
        return ""

    # Get initial caption from BLIP (longer for more detail, but still fast)
    max_tokens = (
        int(os.environ.get("DSS_BLIP_MAX_NEW_TOKENS", "80"))
        if max_new_tokens is None
        else int(max_new_tokens)
    )

    try:
        # Process image and get initial caption
        inputs = processor(img, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        import torch  # Import here to avoid loading if not needed
        with torch.no_grad():  # Disable gradient computation for faster inference
            out = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                num_beams=3,  # Smaller beam for faster initial caption
                do_sample=False,
            )
        
        initial_caption = processor.decode(out[0], skip_special_tokens=True)
        initial_caption = (initial_caption or "").strip()
    except Exception as e:
        logger.exception("BLIP caption generation failed")
        return ""

    if not initial_caption:
        return ""

    # Format the caption directly into structured format (fast, no Ollama needed)
    # This matches document summary format without the delay
    return _format_caption_as_summary(initial_caption)
