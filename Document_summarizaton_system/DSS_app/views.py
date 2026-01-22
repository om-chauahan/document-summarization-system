from django.http import JsonResponse, StreamingHttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login as dj_login, logout as dj_logout
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from typing import Optional
import io
import json
import logging
import os
import shutil
import re
import secrets
import urllib.parse

from .models import StoredDocument, UserCredits, RazorpayTopupOrder

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    from docx import Document as DocxDocument
except Exception:  # pragma: no cover
    DocxDocument = None

import PyPDF2

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None

try:
    from pdf2image import convert_from_bytes
except Exception:  # pragma: no cover
    convert_from_bytes = None

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None

logger = logging.getLogger(__name__)


try:
    import razorpay
except Exception:  # pragma: no cover
    razorpay = None


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def debug_auth(request):
    """Local-dev helper to debug session/cookie auth.

    Not used by the app itself; useful when diagnosing OAuth/session issues.
    """
    user = getattr(request, "user", None)
    return JsonResponse(
        {
            "ok": True,
            "is_authenticated": bool(user and getattr(user, "is_authenticated", False)),
            "user": {
                "username": getattr(user, "username", None),
                "email": getattr(user, "email", None),
            }
            if user and getattr(user, "is_authenticated", False)
            else None,
            "cookies": {
                "sessionid_present": "sessionid" in request.COOKIES,
                "sessionid": request.COOKIES.get("sessionid"),
            },
            "origin": request.headers.get("Origin"),
            "host": request.get_host(),
        }
    )

try:
    # Local LLM summarization via Ollama.
    from .summarization import summarize_text as model_summarize_text
    from .summarization import stream_summary as model_stream_summary
except Exception:  # pragma: no cover
    model_summarize_text = None
    model_stream_summary = None


def _cors_allow(request, response: JsonResponse) -> JsonResponse:
    """Minimal CORS helper for local dev (Django API + Vite frontend).

    We reflect an allowed origin and enable credentials so cookies/sessions
    can work if needed.
    """
    origin = request.headers.get("Origin")
    allowed = {"http://localhost:5173", "http://127.0.0.1:5173"}
    if origin in allowed:
        response["Access-Control-Allow-Origin"] = origin
        response["Vary"] = "Origin"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        response["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    return response


# Google OAuth removed. Re-add standard auth endpoints used by the SPA.


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def login_user(request):
    if request.method == "OPTIONS":
        return JsonResponse({"ok": True})

    data = _get_json_body(request)
    identifier = (data.get("identifier") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return JsonResponse({"ok": False, "error": "Missing credentials."}, status=400)

    user = authenticate(request, username=identifier, password=password)
    if user is None:
        return JsonResponse({"ok": False, "error": "Invalid credentials."}, status=401)

    dj_login(request, user)
    return JsonResponse(
        {
            "ok": True,
            "user": _serialize_user(user),
        }
    )


@require_http_methods(["POST", "OPTIONS"])
def signup_user(request):
    if request.method == "OPTIONS":
        return JsonResponse({"ok": True})

    data = _get_json_body(request)
    first_name = (data.get("firstName") or "").strip()
    last_name = (data.get("lastName") or "").strip()
    mobile = (data.get("mobile") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not mobile:
        return JsonResponse({"ok": False, "error": "Mobile is required."}, status=400)
    if not email:
        return JsonResponse({"ok": False, "error": "Email is required."}, status=400)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "Invalid email."}, status=400)
    if not password:
        return JsonResponse({"ok": False, "error": "Password is required."}, status=400)

    username = mobile
    if User.objects.filter(username=username).exists():
        return JsonResponse({"ok": False, "error": "Mobile already registered."}, status=409)
    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"ok": False, "error": "Email already registered."}, status=409)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    # New accounts start with 100 credits.
    credits_obj = _get_or_create_user_credits(user)
    if credits_obj.credits < 100:
        credits_obj.credits = 100
        credits_obj.save(update_fields=["credits", "updated_at"])

    return JsonResponse(
        {
            "ok": True,
            "user": _serialize_user(user),
        },
        status=201,
    )


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def me_user(request):
    if request.method == "OPTIONS":
        return JsonResponse({"ok": True})

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return JsonResponse({"ok": False, "error": "Not authenticated."}, status=401)

    return JsonResponse(
        {
            "ok": True,
            "user": _serialize_user(user),
        }
    )


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def logout_user(request):
    if request.method == "OPTIONS":
        return JsonResponse({"ok": True})

    dj_logout(request)
    return JsonResponse({"ok": True})


def _require_authenticated_user(request):
    user = getattr(request, "user", None)
    return user if user and getattr(user, "is_authenticated", False) else None


def _get_or_create_user_credits(user) -> UserCredits:
    credits_obj, _ = UserCredits.objects.get_or_create(user=user)
    return credits_obj


def _serialize_user(user) -> dict:
    credits_obj = _get_or_create_user_credits(user)
    return {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "credits": credits_obj.credits,
    }


def _calculate_credits_from_bytes(text_bytes: int) -> int:
    """Calculate credits based on extracted text size in bytes (UTF-8).

    Pricing tiers (more expensive than the previous summary-based pricing):
    - 0-1 KB (0-1,024 bytes): 3 credits
    - 1 KB-5 KB (1,025-5,120 bytes): 5 credits
    - 5 KB-10 KB (5,121-10,240 bytes): 8 credits
    - 10 KB-25 KB (10,241-25,600 bytes): 12 credits
    - 25 KB-50 KB (25,601-51,200 bytes): 18 credits
    - 50 KB-100 KB (51,201-102,400 bytes): 25 credits
    - 100 KB-250 KB (102,401-256,000 bytes): 40 credits
    - 250 KB+ (256,001+ bytes): 60 credits
    """
    if text_bytes <= 0:
        return 3

    size_kb = text_bytes / 1024

    if size_kb <= 1:
        return 3
    elif size_kb <= 5:
        return 5
    elif size_kb <= 10:
        return 8
    elif size_kb <= 25:
        return 12
    elif size_kb <= 50:
        return 18
    elif size_kb <= 100:
        return 25
    elif size_kb <= 250:
        return 40
    else:
        return 60


def _consume_credits(user, cost: int) -> tuple[bool, int]:
    """Atomically consume credits. Returns (ok, remaining)."""
    cost_int = int(cost or 0)
    if cost_int <= 0:
        credits_obj = _get_or_create_user_credits(user)
        return True, credits_obj.credits

    with transaction.atomic():
        credits_obj = UserCredits.objects.select_for_update().get_or_create(user=user)[0]
        if credits_obj.credits < cost_int:
            return False, credits_obj.credits
        credits_obj.credits = int(credits_obj.credits) - cost_int
        credits_obj.save(update_fields=["credits", "updated_at"])
        return True, credits_obj.credits


def _get_razorpay_client_with_error():
    """Return (client, err_code).

    err_code:
      - None (success)
      - "missing_keys"
      - "sdk_missing"
      - "init_failed"
    """
    key_id = getattr(settings, "DSS_RAZORPAY_KEY_ID", "") or os.getenv("DSS_RAZORPAY_KEY_ID", "")
    key_secret = getattr(settings, "DSS_RAZORPAY_KEY_SECRET", "") or os.getenv("DSS_RAZORPAY_KEY_SECRET", "")
    
    # If still not found, read .env file directly as fallback
    if not key_id or not key_secret:
        try:
            from pathlib import Path
            # views.py is in DSS_app/, .env is in project root (Document_summarizaton_system/)
            BASE_DIR = Path(__file__).resolve().parent.parent
            env_path = BASE_DIR / ".env"
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == "DSS_RAZORPAY_KEY_ID" and not key_id:
                                key_id = value
                                logger.info("Loaded DSS_RAZORPAY_KEY_ID from .env file")
                            elif key == "DSS_RAZORPAY_KEY_SECRET" and not key_secret:
                                key_secret = value
                                logger.info("Loaded DSS_RAZORPAY_KEY_SECRET from .env file")
        except Exception as e:
            logger.warning(f"Failed to read Razorpay keys from .env file: {e}")
    
    # Strip whitespace
    key_id = key_id.strip() if key_id else ""
    key_secret = key_secret.strip() if key_secret else ""

    if not key_id or not key_secret:
        return None, "missing_keys"
    if razorpay is None:
        return None, "sdk_missing"
    try:
        return razorpay.Client(auth=(key_id, key_secret)), None
    except Exception:
        logger.exception("Failed to initialize Razorpay client")
        return None, "init_failed"


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def razorpay_config(request):
    if request.method == "OPTIONS":
        return add_cors_headers(JsonResponse({"ok": True}), request)

    user = _require_authenticated_user(request)
    if not user:
        return add_cors_headers(JsonResponse({"ok": False, "error": "Not authenticated."}, status=401), request)

    client, err = _get_razorpay_client_with_error()
    if client is None:
        if err == "sdk_missing":
            return add_cors_headers(
                JsonResponse(
                    {
                        "ok": False,
                        "error": "Razorpay SDK is not installed on the backend server.",
                    },
                    status=503,
                ),
                request,
            )
        if err == "missing_keys":
            return add_cors_headers(
                JsonResponse(
                    {
                        "ok": False,
                        "error": "Razorpay keys are missing. Set DSS_RAZORPAY_KEY_ID and DSS_RAZORPAY_KEY_SECRET.",
                    },
                    status=501,
                ),
                request,
            )
        return add_cors_headers(
            JsonResponse({"ok": False, "error": "Razorpay is not available."}, status=502),
            request,
        )

    # Get key_id using the same logic as _get_razorpay_client_with_error
    key_id = getattr(settings, "DSS_RAZORPAY_KEY_ID", "") or os.getenv("DSS_RAZORPAY_KEY_ID", "")
    
    # If still not found, read .env file directly as fallback
    if not key_id:
        try:
            from pathlib import Path
            BASE_DIR = Path(__file__).resolve().parent.parent
            env_path = BASE_DIR / ".env"
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == "DSS_RAZORPAY_KEY_ID" and not key_id:
                                key_id = value
                                logger.info("Loaded DSS_RAZORPAY_KEY_ID from .env file in razorpay_config")
        except Exception as e:
            logger.warning(f"Failed to read Razorpay key_id from .env file: {e}")
    
    key_id = key_id.strip() if key_id else ""

    return add_cors_headers(
        JsonResponse({"ok": True, "key_id": key_id, "currency": "INR"}),
        request,
    )


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def razorpay_create_order(request):
    if request.method == "OPTIONS":
        return add_cors_headers(JsonResponse({"ok": True}), request)

    user = _require_authenticated_user(request)
    if not user:
        return add_cors_headers(JsonResponse({"ok": False, "error": "Not authenticated."}, status=401), request)

    client, err = _get_razorpay_client_with_error()
    if client is None:
        logger.error(
            "Razorpay create-order unavailable (reason=%s, key_id=%s, key_secret=%s, sdk=%s)",
            err,
            "SET" if (getattr(settings, "DSS_RAZORPAY_KEY_ID", "") or "").strip() else "MISSING",
            "SET" if (getattr(settings, "DSS_RAZORPAY_KEY_SECRET", "") or "").strip() else "MISSING",
            "SET" if razorpay is not None else "MISSING",
        )
        if err == "sdk_missing":
            return add_cors_headers(
                JsonResponse(
                    {
                        "ok": False,
                        "error": "Razorpay SDK is not installed on the backend server.",
                    },
                    status=503,
                ),
                request,
            )
        if err == "missing_keys":
            return add_cors_headers(
                JsonResponse(
                    {
                        "ok": False,
                        "error": "Razorpay keys are missing. Set DSS_RAZORPAY_KEY_ID and DSS_RAZORPAY_KEY_SECRET.",
                    },
                    status=501,
                ),
                request,
            )
        return add_cors_headers(JsonResponse({"ok": False, "error": "Razorpay is not available."}, status=502), request)

    PLAN_CATALOG = {
        "starter": {"name": "Starter", "credits": 100, "amount_inr": 10},
        "plus": {"name": "Plus", "credits": 250, "amount_inr": 20},
        "pro": {"name": "Pro", "credits": 500, "amount_inr": 35},
    }

    data = _get_json_body(request)
    plan_id = (data.get("plan_id") or "").strip().lower()
    if not plan_id or plan_id not in PLAN_CATALOG:
        return add_cors_headers(JsonResponse({"ok": False, "error": "Invalid plan."}, status=400), request)

    plan = PLAN_CATALOG[plan_id]
    amount_paise = int(plan["amount_inr"]) * 100
    currency = "INR"

    try:
        order = client.order.create(
            {
                "amount": amount_paise,
                "currency": currency,
                "payment_capture": 1,
                "notes": {"user_id": str(user.id), "plan_id": plan_id},
            }
        )
    except Exception as e:
        logger.error("Razorpay order create failed: %s", str(e), exc_info=True)
        return add_cors_headers(JsonResponse({"ok": False, "error": "Failed to create order."}, status=502), request)

    try:
        RazorpayTopupOrder.objects.create(
            user=user,
            plan_id=plan_id,
            credits_to_add=int(plan["credits"]),
            amount_paise=amount_paise,
            currency=currency,
            razorpay_order_id=order.get("id"),
            status=RazorpayTopupOrder.STATUS_CREATED,
        )
    except Exception:
        logger.exception("Failed to persist Razorpay top-up order")

    # Get key_id using the same logic as _get_razorpay_client_with_error
    key_id = getattr(settings, "DSS_RAZORPAY_KEY_ID", "") or os.getenv("DSS_RAZORPAY_KEY_ID", "")
    
    # If still not found, read .env file directly as fallback
    if not key_id:
        try:
            from pathlib import Path
            BASE_DIR = Path(__file__).resolve().parent.parent
            env_path = BASE_DIR / ".env"
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == "DSS_RAZORPAY_KEY_ID" and not key_id:
                                key_id = value
        except Exception:
            pass
    
    key_id = key_id.strip() if key_id else ""
    
    return add_cors_headers(
        JsonResponse(
            {
                "ok": True,
                "key_id": key_id,
                "order_id": order.get("id"),
                "amount": order.get("amount"),
                "currency": order.get("currency"),
                "plan_id": plan_id,
                "credits": int(plan["credits"]),
            }
        ),
        request,
    )


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def razorpay_verify_payment(request):
    if request.method == "OPTIONS":
        return add_cors_headers(JsonResponse({"ok": True}), request)

    user = _require_authenticated_user(request)
    if not user:
        return add_cors_headers(JsonResponse({"ok": False, "error": "Not authenticated."}, status=401), request)

    client, err = _get_razorpay_client_with_error()
    if client is None:
        if err == "sdk_missing":
            return add_cors_headers(
                JsonResponse(
                    {
                        "ok": False,
                        "error": "Razorpay SDK is not installed on the backend server.",
                    },
                    status=503,
                ),
                request,
            )
        if err == "missing_keys":
            return add_cors_headers(
                JsonResponse(
                    {
                        "ok": False,
                        "error": "Razorpay keys are missing. Set DSS_RAZORPAY_KEY_ID and DSS_RAZORPAY_KEY_SECRET.",
                    },
                    status=501,
                ),
                request,
            )
        return add_cors_headers(JsonResponse({"ok": False, "error": "Razorpay is not available."}, status=502), request)

    data = _get_json_body(request)
    order_id = (data.get("razorpay_order_id") or "").strip()
    payment_id = (data.get("razorpay_payment_id") or "").strip()
    signature = (data.get("razorpay_signature") or "").strip()
    if not order_id or not payment_id or not signature:
        return add_cors_headers(JsonResponse({"ok": False, "error": "Missing payment fields."}, status=400), request)

    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
    except Exception:
        return add_cors_headers(JsonResponse({"ok": False, "error": "Signature verification failed."}, status=400), request)

    with transaction.atomic():
        topup = (
            RazorpayTopupOrder.objects.select_for_update()
            .filter(razorpay_order_id=order_id, user=user)
            .first()
        )
        if topup is None:
            return add_cors_headers(JsonResponse({"ok": False, "error": "Unknown order."}, status=400), request)

        # Idempotency: don't credit twice.
        if topup.status == RazorpayTopupOrder.STATUS_PAID:
            credits_obj = _get_or_create_user_credits(user)
            return add_cors_headers(
                JsonResponse(
                    {
                        "ok": True,
                        "order_id": order_id,
                        "payment_id": topup.razorpay_payment_id or payment_id,
                        "credits": credits_obj.credits,
                        "credited": False,
                    }
                ),
                request,
            )

        credits_obj = UserCredits.objects.select_for_update().get_or_create(user=user)[0]
        credits_obj.credits = int(credits_obj.credits) + int(topup.credits_to_add)
        credits_obj.save(update_fields=["credits", "updated_at"])

        topup.status = RazorpayTopupOrder.STATUS_PAID
        topup.razorpay_payment_id = payment_id
        topup.paid_at = timezone.now()
        topup.save(update_fields=["status", "razorpay_payment_id", "paid_at"])

    return add_cors_headers(
        JsonResponse(
            {
                "ok": True,
                "order_id": order_id,
                "payment_id": payment_id,
                "credits": credits_obj.credits,
                "credited": True,
            }
        ),
        request,
    )


@csrf_exempt
@require_http_methods(["PUT", "PATCH", "OPTIONS"])
def update_profile(request):
    """Update user profile information."""
    if request.method == "OPTIONS":
        response = JsonResponse({"ok": True})
        return add_cors_headers(response, request)

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        response = JsonResponse({"ok": False, "error": "Not authenticated."}, status=401)
        return add_cors_headers(response, request)

    data = _get_json_body(request)
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email") or "").strip()
    mobile = (data.get("mobile") or "").strip()

    # Validate email if provided
    if email and email != user.email:
        try:
            validate_email(email)
            # Check if email is already taken by another user
            if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                response = JsonResponse({"ok": False, "error": "Email already registered."}, status=409)
                return add_cors_headers(response, request)
        except ValidationError:
            response = JsonResponse({"ok": False, "error": "Invalid email."}, status=400)
            return add_cors_headers(response, request)

    # Validate mobile/username if provided
    if mobile and mobile != user.username:
        mobile = _normalize_mobile(mobile)
        if not mobile:
            response = JsonResponse({"ok": False, "error": "Invalid mobile number."}, status=400)
            return add_cors_headers(response, request)
        # Check if mobile/username is already taken
        if User.objects.filter(username=mobile).exclude(pk=user.pk).exists():
            response = JsonResponse({"ok": False, "error": "Mobile already registered."}, status=409)
            return add_cors_headers(response, request)

    # Update user fields
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if email:
        user.email = email
    if mobile:
        user.username = mobile

    user.save()

    response = JsonResponse(
        {
            "ok": True,
            "user": _serialize_user(user),
        }
    )
    return add_cors_headers(response, request)


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def change_password(request):
    """Change user password."""
    if request.method == "OPTIONS":
        response = JsonResponse({"ok": True})
        return add_cors_headers(response, request)

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        response = JsonResponse({"ok": False, "error": "Not authenticated."}, status=401)
        return add_cors_headers(response, request)

    data = _get_json_body(request)
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        response = JsonResponse({"ok": False, "error": "Current password and new password are required."}, status=400)
        return add_cors_headers(response, request)

    # Verify current password
    if not user.check_password(current_password):
        response = JsonResponse({"ok": False, "error": "Current password is incorrect."}, status=401)
        return add_cors_headers(response, request)

    # Validate new password
    password_error = _validate_password(new_password)
    if password_error:
        response = JsonResponse({"ok": False, "error": password_error}, status=400)
        return add_cors_headers(response, request)

    # Set new password
    user.set_password(new_password)
    user.save()

    # Re-login the user with new password
    dj_login(request, user)

    response = JsonResponse({"ok": True, "message": "Password changed successfully."})
    return add_cors_headers(response, request)


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def delete_account(request):
    """Delete user account."""
    if request.method == "OPTIONS":
        response = JsonResponse({"ok": True})
        return add_cors_headers(response, request)

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        response = JsonResponse({"ok": False, "error": "Not authenticated."}, status=401)
        return add_cors_headers(response, request)

    data = _get_json_body(request)
    password = data.get("password", "")

    if not password:
        response = JsonResponse({"ok": False, "error": "Password is required to delete account."}, status=400)
        return add_cors_headers(response, request)

    # Verify password
    if not user.check_password(password):
        response = JsonResponse({"ok": False, "error": "Incorrect password."}, status=401)
        return add_cors_headers(response, request)

    # Delete user
    user.delete()

    # Logout
    dj_logout(request)

    response = JsonResponse({"ok": True, "message": "Account deleted successfully."})
    return add_cors_headers(response, request)


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def google_login(request):
    """Start Google OAuth flow.
    
    Redirects user to Google's OAuth consent screen.
    """
    if request.method == "OPTIONS":
        response = JsonResponse({"ok": True})
        return add_cors_headers(response, request)
    
    # Get OAuth configuration - try settings first, then os.getenv, then read .env file directly
    client_id = getattr(settings, "DSS_GOOGLE_CLIENT_ID", "") or os.getenv("DSS_GOOGLE_CLIENT_ID", "")
    client_secret = getattr(settings, "DSS_GOOGLE_CLIENT_SECRET", "") or os.getenv("DSS_GOOGLE_CLIENT_SECRET", "")
    redirect_uri = getattr(settings, "DSS_GOOGLE_REDIRECT_URI", "") or os.getenv("DSS_GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback/")
    
    # If still not found, read .env file directly as fallback
    if not client_id or not client_secret:
        try:
            from pathlib import Path
            # views.py is in DSS_app/, .env is in project root (Document_summarizaton_system/)
            # So: parent = DSS_app, parent.parent = Document_summarizaton_system (project root)
            BASE_DIR = Path(__file__).resolve().parent.parent
            env_path = BASE_DIR / ".env"
            logger.info(f"Reading .env from: {env_path} (exists: {env_path.exists()})")
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == "DSS_GOOGLE_CLIENT_ID" and not client_id:
                                client_id = value
                                logger.info("Loaded DSS_GOOGLE_CLIENT_ID from .env file")
                            elif key == "DSS_GOOGLE_CLIENT_SECRET" and not client_secret:
                                client_secret = value
                                logger.info("Loaded DSS_GOOGLE_CLIENT_SECRET from .env file")
                            elif key == "DSS_GOOGLE_REDIRECT_URI" and not redirect_uri:
                                redirect_uri = value
            else:
                logger.warning(f".env file not found at {env_path}")
        except Exception as e:
            logger.error(f"Failed to read .env file directly: {e}", exc_info=True)
    
    # Strip whitespace
    client_id = client_id.strip() if client_id else ""
    client_secret = client_secret.strip() if client_secret else ""
    redirect_uri = redirect_uri.strip() if redirect_uri else ""

    frontend_base = (
        getattr(settings, "DSS_FRONTEND_BASE", "")
        or os.getenv("DSS_FRONTEND_BASE", "")
        or "http://localhost:5173"
    ).rstrip("/")

    # Validate configuration
    if not client_id or not client_secret or not redirect_uri:
        logger.error(
            "Google OAuth configuration missing - "
            f"client_id: {'SET' if client_id else 'MISSING'}, "
            f"client_secret: {'SET' if client_secret else 'MISSING'}, "
            f"redirect_uri: {'SET' if redirect_uri else 'MISSING'}"
        )
        return HttpResponseRedirect(f"{frontend_base}/login?oauth=misconfigured")

    # Get redirect path after login
    next_path = (request.GET.get("next") or "/upload").strip()
    if not next_path or not next_path.startswith("/"):
        next_path = "/upload"

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session["google_oauth_state"] = state
    request.session["google_oauth_next"] = next_path
    request.session.save()

    # Build Google OAuth URL
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": state,
    }
    
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return HttpResponseRedirect(auth_url)


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def google_callback(request):
    """Handle Google OAuth callback.
    
    Exchanges authorization code for access token, fetches user info,
    creates or logs in user, and redirects to frontend.
    """
    if request.method == "OPTIONS":
        response = JsonResponse({"ok": True})
        return add_cors_headers(response, request)

    # Get OAuth configuration - try settings first, then os.getenv, then read .env file directly
    client_id = getattr(settings, "DSS_GOOGLE_CLIENT_ID", "") or os.getenv("DSS_GOOGLE_CLIENT_ID", "")
    client_secret = getattr(settings, "DSS_GOOGLE_CLIENT_SECRET", "") or os.getenv("DSS_GOOGLE_CLIENT_SECRET", "")
    redirect_uri = getattr(settings, "DSS_GOOGLE_REDIRECT_URI", "") or os.getenv("DSS_GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback/")
    
    # If still not found, read .env file directly as fallback
    if not client_id or not client_secret:
        try:
            from pathlib import Path
            # views.py is in DSS_app/, .env is in project root (Document_summarizaton_system/)
            # So: parent = DSS_app, parent.parent = Document_summarizaton_system (project root)
            BASE_DIR = Path(__file__).resolve().parent.parent
            env_path = BASE_DIR / ".env"
            logger.info(f"Reading .env from: {env_path} (exists: {env_path.exists()})")
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == "DSS_GOOGLE_CLIENT_ID" and not client_id:
                                client_id = value
                                logger.info("Loaded DSS_GOOGLE_CLIENT_ID from .env file")
                            elif key == "DSS_GOOGLE_CLIENT_SECRET" and not client_secret:
                                client_secret = value
                                logger.info("Loaded DSS_GOOGLE_CLIENT_SECRET from .env file")
                            elif key == "DSS_GOOGLE_REDIRECT_URI" and not redirect_uri:
                                redirect_uri = value
            else:
                logger.warning(f".env file not found at {env_path}")
        except Exception as e:
            logger.error(f"Failed to read .env file directly: {e}", exc_info=True)
    
    # Strip whitespace
    client_id = client_id.strip() if client_id else ""
    client_secret = client_secret.strip() if client_secret else ""
    redirect_uri = redirect_uri.strip() if redirect_uri else ""

    frontend_base = (
        getattr(settings, "DSS_FRONTEND_BASE", "")
        or os.getenv("DSS_FRONTEND_BASE", "")
        or "http://localhost:5173"
    ).rstrip("/")

    if not client_id or not client_secret or not redirect_uri:
        logger.error("Google OAuth not configured in callback")
        return HttpResponseRedirect(f"{frontend_base}/login?oauth=misconfigured")

    # Verify state parameter (CSRF protection)
    state = request.GET.get("state", "")
    session_state = request.session.get("google_oauth_state", "")
    
    if not state or not session_state or state != session_state:
        logger.warning("Google OAuth state mismatch or missing")
        return HttpResponseRedirect(f"{frontend_base}/login?oauth=failed")

    # Check for error from Google
    error = request.GET.get("error", "")
    if error:
        logger.warning(f"Google OAuth returned error: {error}")
        return HttpResponseRedirect(f"{frontend_base}/login?oauth=failed")

    # Get authorization code
    code = request.GET.get("code", "")
    if not code:
        logger.warning("No authorization code in Google OAuth callback")
        return HttpResponseRedirect(f"{frontend_base}/login?oauth=failed")

    # Check if requests library is available
    if requests is None:
        logger.error("requests library not available")
        return HttpResponseRedirect(f"{frontend_base}/login?oauth=failed")

    try:
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            logger.error("No access token received from Google")
            return HttpResponseRedirect(f"{frontend_base}/login?oauth=failed")

        # Fetch user information from Google
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        userinfo_headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = requests.get(userinfo_url, headers=userinfo_headers, timeout=10)
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()

        # Extract user information
        email = userinfo.get("email", "").strip()
        if not email:
            logger.warning("No email in Google userinfo")
            return HttpResponseRedirect(f"{frontend_base}/login?oauth=noemail")

        first_name = userinfo.get("given_name", "").strip()
        last_name = userinfo.get("family_name", "").strip()

        # Create or get user by email
        # Use email prefix as username, ensure uniqueness
        base_username = email.split("@")[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exclude(email__iexact=email).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user, created = User.objects.get_or_create(
            email__iexact=email,
            defaults={
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        # Update existing user info if needed
        if not created:
            updated = False
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if updated:
                user.save()

        # Log the user in
        dj_login(request, user)
        _get_or_create_user_credits(user)
        logger.info(f"User logged in via Google OAuth: {user.email}")

        # Get redirect path and clean up session
        next_path = request.session.get("google_oauth_next", "/upload")
        if "google_oauth_state" in request.session:
            del request.session["google_oauth_state"]
        if "google_oauth_next" in request.session:
            del request.session["google_oauth_next"]
        request.session.save()

        # Redirect to frontend
        frontend_url = f"{frontend_base}{next_path}"
        return HttpResponseRedirect(frontend_url)

    except requests.RequestException as e:
        logger.error(f"Google OAuth request failed: {str(e)}", exc_info=True)
        return HttpResponseRedirect(f"{frontend_base}/login?oauth=failed")
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}", exc_info=True)
        return HttpResponseRedirect(f"{frontend_base}/login?oauth=failed")


def _normalize_text(text: str) -> str:
    """Light normalization to reduce whitespace noise."""
    return "\n".join(line.rstrip() for line in (text or "").splitlines()).strip()


def extract_text_from_txt_bytes(raw: bytes) -> str:
    """Extract text from a plain text file.

    Tries UTF-8 first, then falls back to latin-1 as a last resort.
    """
    if not raw:
        return ""
    try:
        return _normalize_text(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return _normalize_text(raw.decode("latin-1", errors="ignore"))


def extract_text_from_docx_bytes(raw: bytes) -> str:
    """Extract text from a .docx file using python-docx."""
    if not raw:
        return ""
    if DocxDocument is None:
        logger.warning("DOCX extraction skipped (python-docx not installed)")
        return ""

    try:
        doc = DocxDocument(io.BytesIO(raw))
        parts: list[str] = []
        for p in doc.paragraphs:
            t = (p.text or "").strip()
            if t:
                parts.append(t)
        return _normalize_text("\n".join(parts))
    except Exception:
        logger.exception("DOCX extraction failed")
        return ""


def extract_text_from_image_bytes(raw: bytes) -> str:
    """Extract text from an image via OCR (png/jpg/jpeg)."""
    if not raw:
        return ""
    if pytesseract is None:
        logger.warning("Image OCR skipped (pytesseract not installed)")
        return ""

    try:
        from PIL import Image

        img = Image.open(io.BytesIO(raw))
        txt = pytesseract.image_to_string(img, config="--oem 3 --psm 6") or ""
        return _normalize_text(txt)
    except Exception:
        logger.exception("Image OCR failed")
        return ""


def extract_text_from_uploaded_file(uploaded_file) -> tuple[str, str]:
    """Extract text from an uploaded file.

    Returns: (extracted_text, detected_type)
    """
    name = (uploaded_file.name or "").lower()
    raw = uploaded_file.read()

    if name.endswith(".pdf"):
        text = extract_text_from_pdf_bytes(raw, ocr_if_needed=True)
        return text, "pdf"

    if name.endswith(".txt"):
        return extract_text_from_txt_bytes(raw), "txt"

    if name.endswith(".docx"):
        return extract_text_from_docx_bytes(raw), "docx"

    if name.endswith((".png", ".jpg", ".jpeg")):
        return extract_text_from_image_bytes(raw), "image"

    return "", "unsupported"


def extract_text_from_pdf_bytes(pdf_bytes: bytes, *, ocr_if_needed: bool = True) -> str:
    """Extract text from PDFs.

    Strategy:
    1) Use `pdfplumber` when available (better layout/text extraction than PyPDF2 in many PDFs).
    2) Fallback to PyPDF2 if pdfplumber isn't installed or fails.
    3) If still empty and OCR is enabled, render pages to images and OCR with Tesseract.

    Returns normalized text (may be empty if nothing extractable and OCR unavailable).
    """
    if not pdf_bytes:
        return ""

    extracted_parts: list[str] = []

    # 1) pdfplumber first (best quality for many text-based PDFs)
    if pdfplumber is not None:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    # x_tolerance/y_tolerance can improve spacing in some docs.
                    txt = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                    txt = _normalize_text(txt)
                    if txt:
                        extracted_parts.append(txt)
        except Exception:
            extracted_parts = []

    text = _normalize_text("\n\n".join(extracted_parts))

    # 2) Fallback to PyPDF2
    if not text:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            for page in pdf_reader.pages:
                page_text = page.extract_text() or ""
                page_text = _normalize_text(page_text)
                if page_text:
                    extracted_parts.append(page_text)
            text = _normalize_text("\n\n".join(extracted_parts))
        except Exception:
            text = ""

    # 3) OCR fallback for scanned PDFs
    if ocr_if_needed and not text:
        if convert_from_bytes is None or pytesseract is None:
            logger.warning(
                "OCR fallback skipped because dependencies are missing: convert_from_bytes=%s pytesseract=%s",
                convert_from_bytes is not None,
                pytesseract is not None,
            )
            return ""

        try:
            # Helpful diagnostics: poppler + tesseract availability.
            poppler_hint = shutil.which("pdftoppm") or shutil.which("pdfinfo")
            tesseract_cmd = shutil.which("tesseract")
            logger.info(
                "OCR fallback starting (poppler=%s, tesseract=%s, TESSERACT_CMD=%s)",
                poppler_hint,
                tesseract_cmd,
                getattr(pytesseract.pytesseract, "tesseract_cmd", None),
            )

            # Use a moderate DPI for accuracy; higher DPI = slower/more memory.
            images = convert_from_bytes(pdf_bytes, dpi=250)
            logger.info("OCR fallback rendered %s page image(s)", len(images))
            ocr_parts: list[str] = []
            for img in images:
                # Better defaults for typical scanned documents.
                # psm 6 = assume a single uniform block of text.
                ocr_txt = pytesseract.image_to_string(img, config="--oem 3 --psm 6") or ""
                ocr_txt = _normalize_text(ocr_txt)
                if ocr_txt:
                    ocr_parts.append(ocr_txt)
            text = _normalize_text("\n\n".join(ocr_parts))
            if not text:
                logger.warning(
                    "OCR completed but produced empty text (rendered_pages=%s, tesseract=%s)",
                    len(images) if "images" in locals() else None,
                    tesseract_cmd,
                )
        except Exception as e:
            logger.error("OCR fallback failed: %s", str(e), exc_info=True)
            text = ""

    return text


def normalize_extracted_text(text: str) -> str:
    """Normalize extracted PDF text for display and summarization.

    - normalize newlines
    - collapse multiple spaces/tabs
    - join lines inside a paragraph when they are line-wrapped (heuristic)
    - preserve paragraph breaks (keep at most one blank line between paragraphs)
    """
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse tabs/spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Split into paragraphs (two or more newlines separate paragraphs)
    paras = re.split(r"\n{2,}", text)
    normalized_paras = []

    for p in paras:
        # split by single newlines (these are likely line wraps)
        lines = [ln.strip() for ln in p.split("\n") if ln.strip()]
        if not lines:
            continue

        # Reconstruct paragraph: join lines that look like they were wrapped.
        cur = lines[0]
        for ln in lines[1:]:
            # If the current line ends with a sentence terminator, keep newline.
            if re.search(r"[\.\?\!:\"]$", cur):
                cur = cur + "\n" + ln
                continue

            # If the next line starts with a bullet/number or is all-caps (heading), keep newline.
            if re.match(r"^[-•\*\d+]", ln) or re.match(r"^[A-Z\s]{3,}$", ln):
                cur = cur + "\n" + ln
                continue

            # Otherwise it's likely a line-wrap: join with a space.
            cur = cur + " " + ln

        normalized_paras.append(cur.strip())

    # Re-join paragraphs with a single blank line.
    out = "\n\n".join(normalized_paras)
    # Finally, collapse any accidental >2 newlines to two, and strip edges.
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def add_cors_headers(response, request=None):
    """Add CORS headers to response"""
    # NOTE: When using Django session cookies, we must allow credentials and
    # cannot use a wildcard origin. Reflect a known dev origin.
    # We don't always have the request attached to the response, so just set
    # a permissive dev allowlist for localhost/127.0.0.1.
    # (Origin must match exactly when credentials=true.)
    allowed = {"http://127.0.0.1:5173", "http://localhost:5173"}
    req_origin = None
    if request is not None:
        req_origin = request.headers.get("Origin")

    # When using credentials, the origin must match exactly.
    # Default to localhost (the most common dev setup here).
    allow_origin = "http://localhost:5173"
    if isinstance(req_origin, str) and req_origin in allowed:
        allow_origin = req_origin

    response["Access-Control-Allow-Origin"] = allow_origin
    response["Vary"] = "Origin"
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
    return response


def _get_json_body(request):
    """Best-effort JSON body parser for simple auth endpoints."""
    try:
        import json

        raw = request.body.decode("utf-8") if request.body else ""
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def _normalize_mobile(mobile: str) -> str:
    """Normalize a mobile string to digits-only (keeps it simple for username storage)."""
    mobile = (mobile or "").strip()
    mobile = re.sub(r"\D+", "", mobile)
    return mobile


def _looks_like_email(value: str) -> bool:
    try:
        validate_email(value)
        return True
    except ValidationError:
        return False


def _validate_password(pw: str) -> Optional[str]:
    pw = pw or ""
    if len(pw) < 6:
        return "Password must be at least 6 characters."
    return None


def _looks_like_garbage_ocr(text: str) -> bool:
    """Heuristic to detect unusable OCR output from photos.

    Some images (portraits/scenery) can produce non-empty OCR full of symbols.
    In that case we should fall back to image description.
    """

    src = (text or "").strip()
    if not src:
        return True

    total = len(src)
    letters = sum(1 for c in src if c.isalpha())
    alnum = sum(1 for c in src if c.isalnum())

    # If it's short but mostly clean alphanumerics, accept it as real OCR.
    if total < 18:
        if alnum / max(1, total) >= 0.60 and letters >= 4:
            return False
        return True

    # If almost nothing is alphanumeric, it's likely junk.
    if alnum / max(1, total) < 0.22:
        return True

    # If there are very few letters, it's also likely junk.
    if letters / max(1, total) < 0.18:
        return True

    # Look for word-like tokens; real text tends to have vowels.
    words = re.findall(r"[A-Za-z]{2,}", src)
    if len(words) >= 8:
        vowel_words = sum(1 for w in words if re.search(r"[aeiouAEIOU]", w))
        if vowel_words / max(1, len(words)) < 0.35:
            return True

    # Too many tiny tokens often indicates random OCR noise.
    tokens = re.findall(r"\S+", src)
    if len(tokens) >= 10:
        short = sum(1 for t in tokens if len(t) <= 2)
        if short / max(1, len(tokens)) > 0.65:
            return True

    return False


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def summarize_document(request):
    """
    API endpoint to handle document upload and extract text from PDF files.
    Supported formats: PDF, TXT, DOCX, and images (PNG/JPG) via OCR.
    """
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response, request)

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        response = JsonResponse({"ok": False, "error": "Not authenticated."}, status=401)
        return add_cors_headers(response, request)

    try:
        # Check if file is present in request
        if 'file' not in request.FILES:
            logger.warning("No file provided in request")
            response = JsonResponse({
                'error': 'No file provided'
            }, status=400)
            return add_cors_headers(response, request)

        uploaded_file = request.FILES['file']
        
        # Check if file has a name
        if not uploaded_file.name:
            logger.warning("File has no name")
            response = JsonResponse({
                'error': 'File has no name'
            }, status=400)
            return add_cors_headers(response, request)

        file_name = uploaded_file.name.lower()
        file_size = getattr(uploaded_file, "size", 0)
        logger.info(f"Processing file: {file_name}, Size: {file_size} bytes")

        # We support multiple formats now; file-type validation happens during extraction.

        # Check file size (limit to 50MB)
        if file_size > 50 * 1024 * 1024:
            logger.warning(f"File too large: {file_size} bytes")
            response = JsonResponse({
                'error': 'File size exceeds 50MB limit'
            }, status=400)
            return add_cors_headers(response, request)

        # Read the uploaded document once so we can both extract text and store the document.
        raw_bytes = uploaded_file.read()
        if not isinstance(file_size, int) or file_size == 0:
            file_size = len(raw_bytes)

        # Extract text based on file type.
        file_like = io.BytesIO(raw_bytes)
        file_like.name = uploaded_file.name
        extracted_text, detected_type = extract_text_from_uploaded_file(file_like)

        if detected_type == "unsupported":
            response = JsonResponse(
                {
                    'error': 'Unsupported file type. Supported: PDF, TXT, DOCX, PNG/JPG (OCR).'
                },
                status=400,
            )
            return add_cors_headers(response, request)

        if detected_type == "image" and _looks_like_garbage_ocr(extracted_text):
            # If an image contains no readable text OR OCR output is garbled,
            # try to generate an image description instead of failing.
            try:
                from .image_captioning import describe_image_bytes
                image_description = describe_image_bytes(raw_bytes)
                if image_description.strip():
                    # Calculate credits based on description length
                    summary_bytes = len(image_description.encode("utf-8"))
                    required_credits = _calculate_credits_from_bytes(summary_bytes)
                    ok, remaining = _consume_credits(user, required_credits)
                    if not ok:
                        response = JsonResponse(
                            {
                                'success': False,
                                'error': f'Image description generated but insufficient credits. This requires {required_credits} credits, but you only have {remaining} credits.',
                                'credits': remaining,
                                'required_credits': required_credits,
                            },
                            status=403,
                        )
                        return add_cors_headers(response, request)

                    stored = StoredDocument.objects.create(
                        user=user,
                        original_name=uploaded_file.name,
                        content_type=getattr(uploaded_file, "content_type", "") or "",
                        size_bytes=file_size,
                        detected_type=detected_type,
                        file_bytes=raw_bytes,
                        extracted_text="",
                        summary=image_description,
                    )
                    credits_obj = _get_or_create_user_credits(user)
                    response = JsonResponse(
                        {
                            'success': True,
                            'upload_id': stored.id,
                            'extracted_text': "",
                            'extracted_text_length': 0,
                            'summary': image_description,
                            'file_size_bytes': file_size,
                            'summary_bytes': summary_bytes,
                            'credits_used': required_credits,
                            'credits_remaining': credits_obj.credits,
                            'credits': credits_obj.credits,
                            'summarization_used': False,
                            'result_kind': 'image_description',
                            'detected_type': detected_type,
                            'message': f'Image described successfully. {required_credits} credits used.',
                        },
                        status=200,
                    )
                    return add_cors_headers(response, request)
            except ImportError:
                logger.warning("Image captioning not available (torch/transformers not installed)")
            except Exception as e:
                logger.warning("Image description failed: %s", str(e))

            # Fallback to error if description fails
            response = JsonResponse({'error': 'No usable text was found in the image and image description is not available.'}, status=400)
            return add_cors_headers(response, request)

        if not extracted_text.strip():
            # If an image has no text, try image description
            if detected_type == "image":
                try:
                    from .image_captioning import describe_image_bytes
                    image_description = describe_image_bytes(raw_bytes)
                    if image_description.strip():
                        # Calculate credits based on description length
                        summary_bytes = len(image_description.encode("utf-8"))
                        required_credits = _calculate_credits_from_bytes(summary_bytes)
                        ok, remaining = _consume_credits(user, required_credits)
                        if not ok:
                            response = JsonResponse(
                                {
                                    'success': False,
                                    'error': f'Image description generated but insufficient credits. This requires {required_credits} credits, but you only have {remaining} credits.',
                                    'credits': remaining,
                                    'required_credits': required_credits,
                                },
                                status=403,
                            )
                            return add_cors_headers(response, request)

                        stored = StoredDocument.objects.create(
                            user=user,
                            original_name=uploaded_file.name,
                            content_type=getattr(uploaded_file, "content_type", "") or "",
                            size_bytes=file_size,
                            detected_type=detected_type,
                            file_bytes=raw_bytes,
                            extracted_text="",
                            summary=image_description,
                        )
                        credits_obj = _get_or_create_user_credits(user)
                        response = JsonResponse(
                            {
                                'success': True,
                                'upload_id': stored.id,
                                'extracted_text': "",
                                'extracted_text_length': 0,
                                'summary': image_description,
                                'file_size_bytes': file_size,
                                'summary_bytes': summary_bytes,
                                'credits_used': required_credits,
                                'credits_remaining': credits_obj.credits,
                                'credits': credits_obj.credits,
                                'summarization_used': False,
                                'result_kind': 'image_description',
                                'detected_type': detected_type,
                                'message': f'Image described successfully. {required_credits} credits used.',
                            },
                            status=200,
                        )
                        return add_cors_headers(response, request)
                except ImportError:
                    logger.warning("Image captioning not available (torch/transformers not installed)")
                except Exception as e:
                    logger.warning("Image description failed: %s", str(e))

            # Keep prior error behavior for other file types
            if detected_type == "docx" and DocxDocument is None:
                msg = 'DOCX support is not available on the server. Please install python-docx.'
            elif detected_type == "image" and pytesseract is None:
                msg = 'Image OCR is not available on the server. Please install pytesseract and ensure Tesseract is installed.'
            else:
                msg = 'No text could be extracted from the file.'
            response = JsonResponse({'error': msg}, status=400)
            return add_cors_headers(response, request)

        # Normalize spacing / line-wrapping issues so display and summarization are cleaner.
        try:
            extracted_text = normalize_extracted_text(extracted_text)
        except Exception:
            # Don't fail extraction for normalization issues; log and continue with raw text.
            logger.exception("Failed to normalize extracted text")

        # Check if text was extracted after normalization
        if not extracted_text.strip():
            response = JsonResponse({'error': 'No text could be extracted from the file.'}, status=400)
            return add_cors_headers(response, request)

        logger.info(f"Text extracted successfully. Length: {len(extracted_text)} characters")

        # Summarize using local Ollama model.
        if model_summarize_text is None:
            logger.warning("Summarization unavailable (missing ollama dependency)")
            response = JsonResponse({
                'error': 'Summarization is not available on the server. Please install the ollama python package and ensure Ollama is running (see README).'
            }, status=503)
            response = add_cors_headers(response, request)
            return response

        try:
            summary = model_summarize_text(extracted_text)
        except Exception as e:
            logger.error("Model summarization failed: %s", str(e), exc_info=True)
            response = JsonResponse({
                'error': f'Summarization failed: {str(e)}'
            }, status=500)
            response = add_cors_headers(response, request)
            return response

        # Calculate credits based on EXTRACTED text bytes (UTF-8), not original file size.
        extracted_text_bytes = len(extracted_text.encode("utf-8"))
        summary_bytes = len(summary.encode("utf-8"))
        required_credits = _calculate_credits_from_bytes(extracted_text_bytes)
        logger.info(
            "Summary generated (extracted_bytes=%s, summary_bytes=%s). Required credits=%s",
            extracted_text_bytes,
            summary_bytes,
            required_credits,
        )
        
        # Check and consume credits AFTER summary is generated
        ok, remaining = _consume_credits(user, required_credits)
        if not ok:
            # If insufficient credits, still return the summary but with error message
            logger.warning(f"Insufficient credits after summary generation. Required: {required_credits}, Available: {remaining}")
            response = JsonResponse(
                {
                    'success': True,
                    'extracted_text': extracted_text,
                    'summary': summary,
                    'summary_bytes': summary_bytes,
                    'extracted_text_bytes': extracted_text_bytes,
                    'credits_used': 0,  # No credits deducted
                    'credits_remaining': remaining,
                    'credits': remaining,
                    'summarization_used': True,
                    'extracted_text_length': len(extracted_text),
                    'detected_type': detected_type,
                    'error': f'Summary generated but insufficient credits. This summary requires {required_credits} credits, but you only have {remaining} credits. Please buy more credits to save this summary.',
                    'required_credits': required_credits,
                },
                status=200,
            )
            return add_cors_headers(response, request)

        # Save document only if credits were successfully deducted
        stored = StoredDocument.objects.create(
            user=user,
            original_name=uploaded_file.name,
            content_type=getattr(uploaded_file, "content_type", "") or "",
            size_bytes=file_size,
            detected_type=detected_type,
            file_bytes=raw_bytes,
            extracted_text=extracted_text,
            summary=summary,
        )

        # Get remaining credits after consumption
        credits_obj = _get_or_create_user_credits(user)
        
        response = JsonResponse(
            {
                'success': True,
                'upload_id': stored.id,
                'extracted_text': extracted_text,
                'summary': summary,
                'file_size_bytes': file_size,
                'summary_bytes': summary_bytes,
                'extracted_text_bytes': extracted_text_bytes,
                'credits_used': required_credits,
                'credits_remaining': credits_obj.credits,
                'credits': credits_obj.credits,
                'summarization_used': True,
                'extracted_text_length': len(extracted_text),
                'detected_type': detected_type,
                'message': f'Document summarized successfully. Summary: {summary_bytes} bytes, {required_credits} credits used.',
            },
            status=200,
        )
        return add_cors_headers(response, request)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        response = JsonResponse({
            'error': f'An error occurred while processing the file: {str(e)}'
        }, status=500)
        return add_cors_headers(response, request)


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def summarize_document_stream(request):
    """Streaming API endpoint (SSE) to reduce perceived lag.

    Returns a Server-Sent Events stream:
    - event: meta  (JSON metadata, once)
    - event: token (incremental text)
    - event: done  (signals completion)
    - event: error (signals error)
    """

    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response, request)

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        response = JsonResponse({"ok": False, "error": "Not authenticated."}, status=401)
        return add_cors_headers(response, request)

    if 'file' not in request.FILES:
        response = JsonResponse({'error': 'No file provided'}, status=400)
        return add_cors_headers(response, request)

    uploaded_file = request.FILES['file']
    if not uploaded_file.name:
        response = JsonResponse({'error': 'File has no name'}, status=400)
        return add_cors_headers(response, request)
    
    # Get file size (for display only, credits calculated after summary)
    file_size = getattr(uploaded_file, "size", 0)
    logger.info(f"Stream processing file: {uploaded_file.name}, Size: {file_size} bytes")

    if model_stream_summary is None:
        response = JsonResponse(
            {
                'error': 'Streaming summarization is not available on the server. Please install ollama and ensure Ollama is running.'
            },
            status=503,
        )
        return add_cors_headers(response, request)

    raw_bytes = uploaded_file.read()
    # file_size already calculated above, but ensure it's correct
    if not isinstance(file_size, int) or file_size == 0:
        file_size = len(raw_bytes)

    file_like = io.BytesIO(raw_bytes)
    file_like.name = uploaded_file.name
    extracted_text, detected_type = extract_text_from_uploaded_file(file_like)

    if detected_type == "unsupported":
        response = JsonResponse(
            {
                'error': 'Unsupported file type. Supported: PDF, TXT, DOCX, PNG/JPG (OCR).'
            },
            status=400,
        )
        return add_cors_headers(response, request)
    try:
        extracted_text = normalize_extracted_text(extracted_text)
    except Exception:
        logger.exception("Failed to normalize extracted text")

    if not extracted_text.strip():
        if detected_type == "docx" and DocxDocument is None:
            msg = 'DOCX support is not available on the server. Please install python-docx.'
        elif detected_type == "image" and pytesseract is None:
            msg = 'Image OCR is not available on the server. Please install pytesseract and ensure Tesseract is installed.'
        else:
            msg = 'No text could be extracted from the file.'
        response = JsonResponse({'error': msg}, status=400)
        return add_cors_headers(response, request)

    def sse_pack(event: str, data: str) -> str:
        # SSE format: event + data lines + blank line
        # Ensure data has no bare CR.
        safe = (data or "").replace("\r", "")
        lines = safe.split("\n")
        payload = "\n".join(f"data: {ln}" for ln in lines)
        return f"event: {event}\n{payload}\n\n"

    def event_stream():
        # Send metadata early so the UI can show extracted length.
        meta_json = (
            '{'
            f'"extracted_text_length": {len(extracted_text)},'
            f'"detected_type": "{detected_type}",'
            f'"file_size_bytes": {file_size},'
            '"summarization_used": true'
            '}'
        )
        yield sse_pack("meta", meta_json)

        try:
            summary_parts: list[str] = []
            for chunk in model_stream_summary(extracted_text):
                # Send tokens/chunks as they arrive.
                summary_parts.append(chunk)
                yield sse_pack("token", chunk)
            # Send extracted text at the end so the UI doesn't need a second upload.
            # Remove carriage returns to keep the SSE framing safe.
            yield sse_pack("extracted", extracted_text)

            # Calculate credits based on EXTRACTED text bytes (UTF-8)
            full_summary = "".join(summary_parts)
            extracted_text_bytes = len(extracted_text.encode("utf-8"))
            summary_bytes = len(full_summary.encode("utf-8"))
            required_credits = _calculate_credits_from_bytes(extracted_text_bytes)
            logger.info(
                "Summary generated (extracted_bytes=%s, summary_bytes=%s). Required credits=%s",
                extracted_text_bytes,
                summary_bytes,
                required_credits,
            )
            
            # Check and consume credits AFTER summary is generated
            ok, remaining = _consume_credits(user, required_credits)
            credits_obj = _get_or_create_user_credits(user)
            
            if not ok:
                # If insufficient credits, still send summary but with error
                logger.warning(f"Insufficient credits after summary generation. Required: {required_credits}, Available: {remaining}")
                yield sse_pack("credits", json.dumps({
                    "summary_bytes": summary_bytes,
                    "extracted_text_bytes": extracted_text_bytes,
                    "credits_used": 0,
                    "credits_remaining": remaining,
                    "required_credits": required_credits,
                    "error": f"Insufficient credits. This summary requires {required_credits} credits, but you only have {remaining} credits."
                }))
            else:
                # Save document only if credits were successfully deducted
                try:
                    stored = StoredDocument.objects.create(
                        user=user,
                        original_name=uploaded_file.name,
                        content_type=getattr(uploaded_file, "content_type", "") or "",
                        size_bytes=file_size,
                        detected_type=detected_type,
                        file_bytes=raw_bytes,
                        extracted_text=extracted_text,
                        summary=full_summary,
                    )
                    yield sse_pack("saved", json.dumps({"upload_id": stored.id}))
                except Exception:
                    logger.exception("Failed to persist streamed upload")
                
                # Send credits information
                yield sse_pack("credits", json.dumps({
                    "summary_bytes": summary_bytes,
                    "extracted_text_bytes": extracted_text_bytes,
                    "credits_used": required_credits,
                    "credits_remaining": credits_obj.credits,
                }))

            yield sse_pack("done", "")
        except Exception as e:
            yield sse_pack("error", str(e))

    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"  # helps avoid buffering on some proxies
    return add_cors_headers(resp, request)


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def list_uploads(request):
    if request.method == "OPTIONS":
        response = JsonResponse({"ok": True})
        return add_cors_headers(response, request)

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        response = JsonResponse({"ok": False, "error": "Not authenticated."}, status=401)
        return add_cors_headers(response, request)

    qs = StoredDocument.objects.filter(user=user).order_by("-created_at")
    uploads = [
        {
            "id": u.id,
            "original_name": u.original_name,
            "content_type": u.content_type,
            "size_bytes": u.size_bytes,
            "detected_type": u.detected_type,
            "created_at": u.created_at.isoformat(),
        }
        for u in qs
    ]

    response = JsonResponse({"ok": True, "uploads": uploads})
    return add_cors_headers(response, request)


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def get_upload(request, upload_id: int):
    if request.method == "OPTIONS":
        response = JsonResponse({"ok": True})
        return add_cors_headers(response, request)

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        response = JsonResponse({"ok": False, "error": "Not authenticated."}, status=401)
        return add_cors_headers(response, request)

    try:
        u = StoredDocument.objects.get(id=upload_id, user=user)
    except StoredDocument.DoesNotExist:
        response = JsonResponse({"ok": False, "error": "Not found."}, status=404)
        return add_cors_headers(response, request)

    response = JsonResponse(
        {
            "ok": True,
            "upload": {
                "id": u.id,
                "original_name": u.original_name,
                "content_type": u.content_type,
                "size_bytes": u.size_bytes,
                "detected_type": u.detected_type,
                "created_at": u.created_at.isoformat(),
                "extracted_text": u.extracted_text,
                "summary": u.summary,
            },
        }
    )
    return add_cors_headers(response, request)


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def download_upload(request, upload_id: int):
    if request.method == "OPTIONS":
        response = JsonResponse({"ok": True})
        return add_cors_headers(response, request)

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        response = JsonResponse({"ok": False, "error": "Not authenticated."}, status=401)
        return add_cors_headers(response, request)

    try:
        u = StoredDocument.objects.get(id=upload_id, user=user)
    except StoredDocument.DoesNotExist:
        response = JsonResponse({"ok": False, "error": "Not found."}, status=404)
        return add_cors_headers(response, request)

    safe_name = (u.original_name or "document").replace("\n", " ").replace("\r", " ").replace('"', "")
    resp = JsonResponse({}, status=200)
    # Replace JsonResponse with raw bytes response.
    resp = StreamingHttpResponse(iter([u.file_bytes]), content_type=u.content_type or "application/octet-stream")
    resp["Content-Disposition"] = f'attachment; filename="{safe_name}"'
    return add_cors_headers(resp, request)
