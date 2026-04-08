# Paystack Integration Documentation

## Overview

The POS now uses Paystack's JavaScript inline checkout in the browser. The Python backend prepares a signed checkout session, opens a hosted checkout page, and verifies the transaction afterward with the Paystack REST API.

## Flow

1. Cashier selects `Card` or `Mobile Money`.
2. The GUI calls `POST /api/payments/paystack/initialize`.
3. The backend resolves the customer email, creates a short-lived signed checkout token, and returns a `checkout_url`.
4. The browser opens the checkout page and loads `https://js.paystack.co/v1/inline.js`.
5. Paystack collects the payment in the browser.
6. After success, the browser redirects to the completion page.
7. The GUI can still verify the same reference with `GET /api/payments/paystack/verify/<reference>`.

## Files

`src/utils/paystack.py`
- Builds checkout session payloads
- Generates unique references
- Verifies Paystack transactions over HTTP

`src/routes/payments.py`
- `POST /api/payments/paystack/initialize`
- `GET /api/payments/paystack/checkout/<token>`
- `GET /api/payments/paystack/complete/<token>`
- `GET /api/payments/paystack/verify/<reference>`

`src/gui/cashier.py`
- Opens the returned `checkout_url`
- Keeps the manual verify step available as a fallback

## Environment

```env
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
PAYSTACK_SECRET_KEY=sk_test_your_secret_key
PAYSTACK_BASE_URL=https://api.paystack.co
PAYSTACK_CHECKOUT_TOKEN_MAX_AGE=900
```

## Initialize Request

```json
{
  "amount": 500.0,
  "method": "card",
  "customer_name": "John Doe",
  "email": "john@example.com",
  "phone": "08012345678",
  "metadata": {"order_id": "123"}
}
```

The response includes:

```json
{
  "reference": "POS-ABC123...",
  "checkout_url": "http://localhost:5000/api/payments/paystack/checkout/...",
  "authorization_url": "http://localhost:5000/api/payments/paystack/checkout/...",
  "complete_url": "http://localhost:5000/api/payments/paystack/complete/..."
}
```

## Notes

- Email is still optional in the cashier UI; the backend generates a fallback email from the customer name.
- The checkout and completion pages are public because they must be reachable from the browser.
- The manual verify endpoint remains available for the POS workflow and split payment checks.

## Testing

The simplest verification is:

```python
from src.utils.paystack import PaystackClient

client = PaystackClient("sk_test_your_secret_key")
session = client.build_checkout_session(
    amount=500,
    email="john@example.com",
    method="card",
    customer_name="John Doe",
)
print(session["reference"])
print(session["amount_kobo"])
```

## Troubleshooting

- If the checkout page does not open, check that the browser can load `https://js.paystack.co/v1/inline.js`.
- If verification fails, confirm that `PAYSTACK_SECRET_KEY` is correct and the reference matches the checkout session.
- If the completion page says the session is invalid, the signed token likely expired; increase `PAYSTACK_CHECKOUT_TOKEN_MAX_AGE` if needed.
