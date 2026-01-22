from __future__ import annotations

from urllib.parse import urlparse

from django.conf import settings


class DevCorsMiddleware:
    """Minimal CORS middleware for local dev.

    Why this exists:
    - The project uses simple function views (not DRF) and manually adds CORS
      headers in many endpoints.
    - It's easy to miss a path or return inconsistent headers.

    This middleware makes CORS behavior consistent across *all* responses.

    Notes:
    - We only allow known dev origins (Vite).
    - We always set Vary: Origin when we reflect an origin.
    - We support preflight OPTIONS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Support either an explicit setting or fall back to localhost/127.
        frontend_base = getattr(settings, "DSS_FRONTEND_BASE", "http://localhost:5173")
        frontend_origin = _origin(frontend_base) or "http://localhost:5173"

        self.allowed = {
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            frontend_origin,
        }

    def __call__(self, request):
        # Handle preflight quickly.
        if request.method == "OPTIONS":
            response = self.get_response(request)
            return self._add_headers(request, response)

        response = self.get_response(request)
        return self._add_headers(request, response)

    def _add_headers(self, request, response):
        origin = request.headers.get("Origin")
        if origin and origin in self.allowed:
            response["Access-Control-Allow-Origin"] = origin
            response["Vary"] = "Origin"
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
            response["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"

        return response


def _origin(url: str) -> str | None:
    """Return scheme://host[:port] for a URL-like string."""
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return None
    return None
