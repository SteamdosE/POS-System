"""Paystack payment endpoints."""

import requests as http_requests
from flask import Blueprint, current_app, request

from src.utils.auth import any_authenticated
from src.utils.helpers import error_response, success_response

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

_PAYSTACK_BASE_URL = "https://api.paystack.co"


def _get_secret_key() -> str:
    """Return the configured Paystack secret key, or an empty string if absent."""
    return current_app.config.get("PAYSTACK_SECRET_KEY") or ""


def _paystack_headers(secret_key: str) -> dict:
    return {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }


@payments_bp.route("/paystack/initialize", methods=["POST"])
@any_authenticated
def initialize_payment():
    """Initialize a Paystack transaction.

    Request JSON body::

        {
            "email": "customer@example.com",
            "amount": 1500.00,
            "reference": "optional-custom-ref"
        }

    Amount should be in the local currency unit (e.g. KES). It is converted to
    the smallest unit (×100) before being sent to Paystack.

    Returns:
        200: ``authorization_url``, ``access_code``, ``reference``.
        400: Validation error.
        500: Paystack is not configured on this server.
        502: Paystack API unreachable or timed out.
    """
    secret_key = _get_secret_key()
    if not secret_key:
        return error_response("Paystack is not configured on this server", 500)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    email = data.get("email")
    amount = data.get("amount")

    if not email:
        return error_response("'email' is required", 400)
    if amount is None:
        return error_response("'amount' is required", 400)

    try:
        amount_subunit = int(float(amount) * 100)
        if amount_subunit <= 0:
            raise ValueError("amount must be positive")
    except (ValueError, TypeError):
        return error_response("'amount' must be a positive number", 400)

    payload: dict = {"email": email, "amount": amount_subunit}
    if data.get("reference"):
        payload["reference"] = str(data["reference"])

    try:
        resp = http_requests.post(
            f"{_PAYSTACK_BASE_URL}/transaction/initialize",
            json=payload,
            headers=_paystack_headers(secret_key),
            timeout=30,
        )
        resp.raise_for_status()
        ps_data = resp.json().get("data", {})
    except http_requests.exceptions.Timeout:
        return error_response("Paystack request timed out", 502)
    except http_requests.exceptions.RequestException as exc:
        current_app.logger.error("Paystack initialize error: %s", exc)
        return error_response("Failed to reach Paystack", 502)

    return success_response(
        {
            "authorization_url": ps_data.get("authorization_url"),
            "access_code": ps_data.get("access_code"),
            "reference": ps_data.get("reference"),
        },
        "Payment initialized",
    )


@payments_bp.route("/paystack/verify/<string:reference>", methods=["GET"])
@any_authenticated
def verify_payment(reference: str):
    """Verify a Paystack transaction by its reference.

    Args:
        reference: The transaction reference returned by :func:`initialize_payment`.

    Returns:
        200: Transaction ``status``, ``reference``, ``amount``, ``currency``,
             ``paid_at``, and ``channel``.
        500: Paystack is not configured on this server.
        502: Paystack API unreachable or timed out.
    """
    secret_key = _get_secret_key()
    if not secret_key:
        return error_response("Paystack is not configured on this server", 500)

    try:
        resp = http_requests.get(
            f"{_PAYSTACK_BASE_URL}/transaction/verify/{reference}",
            headers=_paystack_headers(secret_key),
            timeout=30,
        )
        resp.raise_for_status()
        ps_data = resp.json().get("data", {})
    except http_requests.exceptions.Timeout:
        return error_response("Paystack request timed out", 502)
    except http_requests.exceptions.RequestException as exc:
        current_app.logger.error("Paystack verify error: %s", exc)
        return error_response("Failed to verify payment with Paystack", 502)

    return success_response(
        {
            "status": ps_data.get("status"),
            "reference": ps_data.get("reference"),
            "amount": (ps_data.get("amount") or 0) / 100,
            "currency": ps_data.get("currency"),
            "paid_at": ps_data.get("paid_at"),
            "channel": ps_data.get("channel"),
        },
        "Payment verified",
    )
