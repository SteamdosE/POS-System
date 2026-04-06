"""Paystack payment helpers for the JS inline checkout flow."""

from __future__ import annotations

import logging
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import uuid4

import requests


logger = logging.getLogger(__name__)

DEFAULT_PAYSTACK_API_BASE = "https://api.paystack.co"
DEFAULT_PAYSTACK_TOKEN_SALT = "paystack-js-checkout"


class PaystackError(Exception):
    """Raised when a Paystack operation fails."""


class PaystackClient:
    """Helper for Paystack checkout session data and transaction verification."""

    def __init__(self, secret_key: str, public_key: str = "", base_url: str = DEFAULT_PAYSTACK_API_BASE) -> None:
        self.secret_key = (secret_key or "").strip()
        self.public_key = (public_key or "").strip()
        self.base_url = (base_url or DEFAULT_PAYSTACK_API_BASE).rstrip("/")

    @property
    def is_configured(self) -> bool:
        """Check if the Paystack secret key is available."""
        return bool(self.secret_key)

    @staticmethod
    def amount_to_kobo(amount: Decimal | float | int | str) -> int:
        """Convert an amount in naira to kobo."""
        value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if value <= 0:
            raise PaystackError("Amount must be greater than 0")
        return int(value * 100)

    @staticmethod
    def generate_reference(prefix: str = "POS") -> str:
        """Generate a short unique payment reference."""
        cleaned_prefix = re.sub(r"[^A-Z0-9]+", "-", prefix.upper()).strip("-") if prefix else "POS"
        return f"{cleaned_prefix}-{uuid4().hex[:16].upper()}"

    def build_checkout_session(
        self,
        *,
        amount: Decimal | float | int | str,
        email: str,
        method: str,
        customer_name: str,
        currency: str = "NGN",
        phone: str = "",
        metadata: dict[str, Any] | None = None,
        reference: str | None = None,
    ) -> dict[str, Any]:
        """Build a normalized payload for the Paystack JS checkout page."""
        normalized_method = (method or "").strip().lower()
        if normalized_method not in {"card", "mobile", "paystack"}:
            raise PaystackError("method must be one of 'card', 'mobile', or 'paystack'")

        normalized_email = (email or "").strip()
        if not normalized_email:
            raise PaystackError("Email is required")

        normalized_name = (customer_name or "").strip()
        if not normalized_name:
            raise PaystackError("Customer name is required")

        normalized_currency = (currency or "NGN").strip().upper()
        if not normalized_currency:
            normalized_currency = "NGN"

        if normalized_method == "card":
            channels = ["card"]
        elif normalized_method == "mobile":
            channels = ["mobile_money"]
        else:
            channels = ["card", "mobile_money"]
        checkout_metadata: dict[str, Any] = dict(metadata or {})
        checkout_metadata.setdefault("customer_name", normalized_name)
        checkout_metadata.setdefault("payment_method", normalized_method)
        if phone:
            checkout_metadata.setdefault("phone", phone)

        return {
            "amount": float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "amount_kobo": self.amount_to_kobo(amount),
            "currency": normalized_currency,
            "email": normalized_email,
            "customer_name": normalized_name,
            "method": normalized_method,
            "channels": channels,
            "phone": phone,
            "metadata": checkout_metadata,
            "reference": reference or self.generate_reference("POS"),
        }

    def verify_transaction(self, reference: str) -> dict[str, Any]:
        """Verify a Paystack transaction by reference using the HTTP API."""
        if not self.is_configured:
            raise PaystackError("Paystack is not configured")
        if not reference:
            raise PaystackError("Reference is required")

        url = f"{self.base_url}/transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {self.secret_key}", "Content-Type": "application/json"}

        try:
            logger.debug("Verifying Paystack transaction: %s", reference)
            response = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as exc:
            logger.error("Paystack verify failed: %s", exc)
            raise PaystackError(f"Failed to verify transaction: {exc}") from exc

        try:
            payload = response.json()
        except Exception as exc:
            raise PaystackError(f"Invalid Paystack response: {exc}") from exc

        if not response.ok:
            message = payload.get("message") if isinstance(payload, dict) else response.text
            raise PaystackError(message or f"Paystack verification failed ({response.status_code})")

        if not payload.get("status"):
            raise PaystackError(payload.get("message", "Transaction verification failed"))

        data = payload.get("data") or {}
        if not data:
            raise PaystackError("No transaction data in Paystack response")

        return data
