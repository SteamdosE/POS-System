"""Payment record endpoints."""

from decimal import Decimal
import json
import os
import re

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import Blueprint, current_app, render_template_string, request, url_for

from src.models.payment import Payment
from src.utils.auth import any_authenticated, manager_or_admin_required
from src.utils.helpers import success_response, error_response, paginate_query
from src.utils.paystack import PaystackClient, PaystackError

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

DEFAULT_PAYSTACK_EMAIL = "donniecarey79564@suffermail.com"


def _paystack_client() -> PaystackClient:
    return PaystackClient(
        secret_key=current_app.config.get("PAYSTACK_SECRET_KEY", ""),
        public_key=current_app.config.get("PAYSTACK_PUBLIC_KEY", ""),
        base_url=current_app.config.get("PAYSTACK_BASE_URL", "https://api.paystack.co"),
    )


def _checkout_serializer() -> URLSafeTimedSerializer:
    secret_key = current_app.config.get("SECRET_KEY") or current_app.secret_key
    if not secret_key:
        raise PaystackError("Application secret key is not configured")
    return URLSafeTimedSerializer(secret_key, salt="paystack-js-checkout")


def _encode_checkout_session(payload: dict) -> str:
    return _checkout_serializer().dumps(payload)


def _decode_checkout_session(token: str) -> dict:
    max_age = int(current_app.config.get("PAYSTACK_CHECKOUT_TOKEN_MAX_AGE", 900))
    try:
        return _checkout_serializer().loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise PaystackError("Paystack checkout session has expired") from exc
    except BadSignature as exc:
        raise PaystackError("Invalid Paystack checkout session") from exc


def _resolve_paystack_email(raw_email: str, customer_name: str) -> str:
    """Return a valid email for Paystack, using a fixed default when email is missing."""
    email = (raw_email or "").strip()
    if email and "@" in email:
        return email

    return DEFAULT_PAYSTACK_EMAIL


def _resolve_app_currency() -> str:
    """Resolve currency from GUI settings first, then backend config fallback."""
    default_currency = str(current_app.config.get("PAYSTACK_CURRENCY") or "NGN").upper()

    settings_path = os.path.join(current_app.root_path, "gui", "app_settings.json")
    try:
        with open(settings_path, "r", encoding="utf-8") as settings_file:
            payload = json.load(settings_file)
        if isinstance(payload, dict):
            code = str(payload.get("currency_code") or "").strip().upper()
            if code:
                return code
    except (OSError, ValueError, TypeError):
        pass

    return default_currency


@payments_bp.route("", methods=["GET"])
@manager_or_admin_required
def list_payments():
    """List payment records with pagination."""
    query = Payment.query.order_by(Payment.created_at.desc())
    return success_response(paginate_query(query))


@payments_bp.route("/<int:payment_id>", methods=["GET"])
@any_authenticated
def get_payment(payment_id: int):
    """Get a payment record by ID."""
    payment = Payment.query.get(payment_id)
    if not payment:
        return error_response("Payment not found", 404)
    return success_response(payment.to_dict())


@payments_bp.route("/sale/<int:sale_id>", methods=["GET"])
@any_authenticated
def list_sale_payments(sale_id: int):
    """List all payments recorded for a sale."""
    payments = Payment.query.filter_by(sale_id=sale_id).order_by(Payment.created_at.asc()).all()
    return success_response({"payments": [payment.to_dict() for payment in payments]})


@payments_bp.route("/paystack/initialize", methods=["POST"])
@any_authenticated
def initialize_paystack_payment():
    """Initialize a Paystack payment transaction for card/mobile money."""
    data = request.get_json(silent=True) or {}

    try:
        amount = Decimal(str(data.get("amount", 0)))
    except Exception:
        return error_response("amount must be numeric", 400)
    if amount <= 0:
        return error_response("amount must be greater than 0", 400)

    customer_name = (data.get("customer_name") or "").strip()
    email = _resolve_paystack_email(data.get("email") or "", customer_name)
    if not email:
        return error_response("customer_name is required when email is not provided", 400)

    method = (data.get("method") or "").strip().lower()
    if method not in {"card", "mobile", "paystack"}:
        return error_response("method must be one of 'card', 'mobile', or 'paystack'", 400)

    phone = re.sub(r"\D", "", str(data.get("phone") or ""))
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    client = _paystack_client()

    if not client.is_configured:
        return error_response("Paystack is not configured on this server", 500)

    try:
        currency_code = _resolve_app_currency()
        session = client.build_checkout_session(
            amount=amount,
            email=email,
            method=method,
            customer_name=customer_name,
            currency=currency_code,
            phone=phone,
            metadata=metadata or None,
        )
        token = _encode_checkout_session(session)
        checkout_url = url_for("payments.paystack_checkout", token=token, _external=True)
        complete_url = url_for("payments.paystack_complete", token=token, _external=True)
        return success_response(
            {
                "reference": session.get("reference"),
                "checkout_url": checkout_url,
                "authorization_url": checkout_url,
                "complete_url": complete_url,
                "amount": float(session.get("amount", amount)),
                "currency": session.get("currency", "NGN"),
                "method": session.get("method"),
            },
            "Paystack checkout ready",
            201,
        )
    except PaystackError as exc:
        return error_response(str(exc), 400)


@payments_bp.route("/paystack/checkout/<string:token>", methods=["GET"])
def paystack_checkout(token: str):
        """Render the Paystack JS checkout page."""
        client = _paystack_client()
        if not client.is_configured:
                return render_template_string(
                        """
                        <!DOCTYPE html>
                        <html>
                        <head><title>Paystack Checkout</title></head>
                        <body style="font-family: Arial, sans-serif; padding: 32px;">
                            <h2>Paystack is not configured on this server</h2>
                        </body>
                        </html>
                        """
                ), 500

        try:
                session = _decode_checkout_session(token)
        except PaystackError as exc:
                return render_template_string(
                        """
                        <!DOCTYPE html>
                        <html>
                        <head><title>Paystack Checkout</title></head>
                        <body style="font-family: Arial, sans-serif; padding: 32px;">
                            <h2>Checkout session error</h2>
                            <p>{{ message }}</p>
                        </body>
                        </html>
                        """,
                        message=str(exc),
                ), 400

        complete_url = url_for("payments.paystack_complete", token=token, _external=True)
        public_key = current_app.config.get("PAYSTACK_PUBLIC_KEY", "")

        return render_template_string(
                """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="utf-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1" />
                    <title>Paystack Checkout</title>
                    <script src="https://js.paystack.co/v1/inline.js"></script>
                    <style>
                        :root { color-scheme: light; }
                        body {
                            margin: 0;
                            min-height: 100vh;
                            display: grid;
                            place-items: center;
                            font-family: Arial, Helvetica, sans-serif;
                            background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 50%, #0f766e 100%);
                            color: #e5e7eb;
                        }
                        .card {
                            width: min(560px, calc(100vw - 32px));
                            background: rgba(15, 23, 42, 0.92);
                            border: 1px solid rgba(255,255,255,0.08);
                            border-radius: 24px;
                            padding: 28px;
                            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
                            backdrop-filter: blur(12px);
                        }
                        .eyebrow { text-transform: uppercase; letter-spacing: .18em; font-size: 12px; color: #93c5fd; }
                        h1 { margin: 10px 0 8px; font-size: 30px; }
                        .amount { font-size: 28px; font-weight: 700; color: #f8fafc; margin: 18px 0 8px; }
                        .meta { line-height: 1.7; color: #cbd5e1; }
                        .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 24px; }
                        button {
                            appearance: none;
                            border: 0;
                            border-radius: 14px;
                            padding: 14px 18px;
                            font-size: 15px;
                            font-weight: 700;
                            cursor: pointer;
                        }
                        .primary { background: #38bdf8; color: #082f49; }
                        .secondary { background: transparent; color: #e2e8f0; border: 1px solid rgba(226,232,240,.2); }
                        .status { margin-top: 18px; min-height: 22px; color: #f8fafc; }
                        .hint { margin-top: 10px; color: #94a3b8; font-size: 13px; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <div class="eyebrow">Secure Payment</div>
                        <h1>{{ method_label }} checkout</h1>
                        <div class="amount">{{ amount_text }}</div>
                        <div class="meta">
                            Customer: <strong>{{ customer_name }}</strong><br />
                            Email: <strong>{{ email }}</strong><br />
                            Reference: <strong>{{ reference }}</strong>
                        </div>
                        <div class="actions">
                            <button class="primary" id="pay-button">Pay now</button>
                            <button class="secondary" id="retry-button" type="button">Reload checkout</button>
                        </div>
                        <div class="status" id="status">Opening Paystack checkout...</div>
                        <div class="hint">If the payment modal does not appear automatically, click Pay now.</div>
                    </div>

                    <script>
                        const checkout = {{ session | tojson }};
                        const publicKey = {{ public_key | tojson }};
                        const completeUrl = {{ complete_url | tojson }};

                        function setStatus(message) {
                            document.getElementById('status').textContent = message;
                        }

                        function launchCheckout() {
                            if (!window.PaystackPop) {
                                setStatus('Paystack checkout library failed to load. Check your network connection.');
                                return;
                            }

                            const handler = PaystackPop.setup({
                                key: publicKey,
                                email: checkout.email,
                                amount: checkout.amount_kobo,
                                currency: checkout.currency,
                                ref: checkout.reference,
                                channels: checkout.channels,
                                metadata: checkout.metadata,
                                callback: function(response) {
                                    setStatus('Payment completed. Verifying transaction...');
                                    window.location.href = completeUrl + '?reference=' + encodeURIComponent(response.reference);
                                },
                                onClose: function() {
                                    setStatus('Checkout closed. You can reopen it when ready.');
                                }
                            });

                            handler.openIframe();
                        }

                        document.getElementById('pay-button').addEventListener('click', launchCheckout);
                        document.getElementById('retry-button').addEventListener('click', function() {
                            window.location.reload();
                        });

                        window.addEventListener('load', launchCheckout);
                    </script>
                </body>
                </html>
                """,
                session=session,
                public_key=public_key,
                complete_url=complete_url,
                method_label="Mobile Money" if session.get("method") == "mobile" else "Card",
                amount_text=f"{session.get('currency', 'NGN')} {session.get('amount', 0):,.2f}",
                customer_name=session.get("customer_name", "Customer"),
                email=session.get("email", ""),
                reference=session.get("reference", ""),
        )


@payments_bp.route("/paystack/complete/<string:token>", methods=["GET"])
def paystack_complete(token: str):
        """Verify a completed Paystack checkout and render the result page."""
        client = _paystack_client()
        if not client.is_configured:
                return render_template_string(
                        """
                        <!DOCTYPE html>
                        <html>
                        <head><title>Payment Verification</title></head>
                        <body style="font-family: Arial, sans-serif; padding: 32px;">
                            <h2>Paystack is not configured on this server</h2>
                        </body>
                        </html>
                        """
                ), 500

        try:
                session = _decode_checkout_session(token)
        except PaystackError as exc:
                return render_template_string(
                        """
                        <!DOCTYPE html>
                        <html>
                        <head><title>Payment Verification</title></head>
                        <body style="font-family: Arial, sans-serif; padding: 32px;">
                            <h2>Verification error</h2>
                            <p>{{ message }}</p>
                        </body>
                        </html>
                        """,
                        message=str(exc),
                ), 400

        reference = (request.args.get("reference") or session.get("reference") or "").strip()
        if not reference:
                return render_template_string(
                        """
                        <!DOCTYPE html>
                        <html>
                        <head><title>Payment Verification</title></head>
                        <body style="font-family: Arial, sans-serif; padding: 32px;">
                            <h2>Missing reference</h2>
                            <p>The Paystack reference was not returned by the checkout modal.</p>
                        </body>
                        </html>
                        """
                ), 400

        try:
                result = client.verify_transaction(reference)
                paid = (result.get("status") or "").lower() == "success"
                amount_kobo = result.get("amount")
                paid_amount = Decimal(str(amount_kobo)) / Decimal("100") if isinstance(amount_kobo, (int, float, str)) else None
                expected_amount = Decimal(str(session.get("amount", 0)))

                if not paid:
                        raise PaystackError("Transaction is not successful yet")
                if paid_amount is not None and paid_amount + Decimal("0.01") < expected_amount:
                        raise PaystackError("Verified amount is less than expected amount")

                return render_template_string(
                        """
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="utf-8" />
                            <meta name="viewport" content="width=device-width, initial-scale=1" />
                            <title>Payment Verified</title>
                            <style>
                                body {
                                    margin: 0;
                                    min-height: 100vh;
                                    display: grid;
                                    place-items: center;
                                    font-family: Arial, Helvetica, sans-serif;
                                    background: linear-gradient(135deg, #052e16 0%, #14532d 48%, #166534 100%);
                                    color: #ecfdf5;
                                }
                                .card {
                                    width: min(560px, calc(100vw - 32px));
                                    background: rgba(6, 78, 59, 0.92);
                                    border-radius: 24px;
                                    padding: 28px;
                                    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
                                }
                                h1 { margin: 0 0 12px; font-size: 30px; }
                                .meta { line-height: 1.8; color: #d1fae5; }
                            </style>
                        </head>
                        <body>
                            <div class="card">
                                <h1>Payment verified</h1>
                                <div class="meta">
                                    Reference: <strong>{{ reference }}</strong><br />
                                    Amount: <strong>{{ amount_text }}</strong><br />
                                    Customer: <strong>{{ customer_name }}</strong><br />
                                    You can return to the POS screen now.
                                </div>
                            </div>
                        </body>
                        </html>
                        """,
                        reference=reference,
                        amount_text=f"{session.get('currency', 'NGN')} {Decimal(str(session.get('amount', 0))):,.2f}",
                        customer_name=session.get("customer_name", "Customer"),
                )
        except PaystackError as exc:
                return render_template_string(
                        """
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="utf-8" />
                            <meta name="viewport" content="width=device-width, initial-scale=1" />
                            <title>Payment Verification Failed</title>
                            <style>
                                body {
                                    margin: 0;
                                    min-height: 100vh;
                                    display: grid;
                                    place-items: center;
                                    font-family: Arial, Helvetica, sans-serif;
                                    background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 50%, #991b1b 100%);
                                    color: #fef2f2;
                                }
                                .card {
                                    width: min(560px, calc(100vw - 32px));
                                    background: rgba(69, 10, 10, 0.92);
                                    border-radius: 24px;
                                    padding: 28px;
                                    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
                                }
                                h1 { margin: 0 0 12px; font-size: 30px; }
                            </style>
                        </head>
                        <body>
                            <div class="card">
                                <h1>Payment verification failed</h1>
                                <p>{{ message }}</p>
                            </div>
                        </body>
                        </html>
                        """,
                        message=str(exc),
                ), 400
@payments_bp.route("/paystack/verify/<string:reference>", methods=["GET"])
@any_authenticated
def verify_paystack_payment(reference: str):
    """Verify a Paystack transaction by reference."""
    client = _paystack_client()
    if not client.is_configured:
        return error_response("Paystack is not configured on this server", 500)

    try:
        result = client.verify_transaction(reference)
    except PaystackError as exc:
        return error_response(str(exc), 400)

    paid = (result.get("status") or "").lower() == "success"
    amount = result.get("amount")
    amount_major = float(amount) / 100 if isinstance(amount, (int, float)) else None

    return success_response(
        {
            "paid": paid,
            "reference": result.get("reference"),
            "gateway_status": result.get("gateway_response"),
            "channel": result.get("channel"),
            "currency": result.get("currency"),
            "amount": amount_major,
            "raw_status": result.get("status"),
        },
        "Paystack transaction verified",
    )
