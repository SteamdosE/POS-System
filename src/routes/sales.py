"""Sales endpoints: checkout, listing, and reporting."""

from datetime import datetime, timezone, date
from decimal import Decimal

from flask import Blueprint, request, current_app
from sqlalchemy import func

from src.db import db
from src.models.product import Product
from src.models.sale import Sale, SaleItem
from src.models.customer import Customer, SaleCustomer
from src.models.payment import Payment
from src.utils.auth import any_authenticated, manager_or_admin_required
from src.utils.helpers import success_response, error_response, paginate_query
from src.utils.paystack import PaystackClient, PaystackError
from flask_jwt_extended import get_jwt_identity

sales_bp = Blueprint("sales", __name__, url_prefix="/api/sales")
DEFAULT_TAX_RATE = Decimal("0.10")
LOYALTY_POINTS_THRESHOLD = 1000
LOYALTY_DISCOUNT_RATE = Decimal("0.05")


def _paystack_client() -> PaystackClient:
    return PaystackClient(
        secret_key=current_app.config.get("PAYSTACK_SECRET_KEY", ""),
        base_url=current_app.config.get("PAYSTACK_BASE_URL", "https://api.paystack.co"),
    )


def _verify_paystack_reference(reference: str, expected_amount: Decimal) -> tuple[bool, str]:
    """Verify Paystack reference status and expected amount."""
    client = _paystack_client()
    if not client.is_configured:
        return False, "Paystack is not configured on this server"
    if not reference:
        return False, "Payment reference is required"

    try:
        result = client.verify_transaction(reference)
    except PaystackError as exc:
        return False, str(exc)

    if (result.get("status") or "").lower() != "success":
        return False, "Paystack transaction is not successful"

    amount_kobo = result.get("amount")
    if not isinstance(amount_kobo, (int, float)):
        return False, "Paystack amount is missing"

    paid_amount = Decimal(str(amount_kobo)) / Decimal("100")
    if paid_amount + Decimal("0.01") < expected_amount:
        return False, "Paystack paid amount is less than expected amount"

    return True, "verified"


@sales_bp.route("", methods=["POST"])
@any_authenticated
def create_sale():
    """Process a new sale / checkout.

    Request JSON body::

        {
            "payment_method": "cash|card|mobile|split",
            "customer_id": int,                    (optional)
            "discount": float,                     (optional)
            "tax_rate": float,                     (optional, default 0.10)
            "amount_tendered": float,              (optional, cash only)
            "payments": [                          (required for split)
                {"method": "cash|card|mobile", "amount": float, "reference": "string"},
                ...
            ],
            "items": [
                {"product_id": int, "quantity": int},
                ...
            ]
        }

    Returns:
        201: Sale created with full item details.
        400: Validation error or insufficient stock.
        404: Product not found.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    items_data = data.get("items")
    if not items_data or not isinstance(items_data, list):
        return error_response("'items' must be a non-empty list", 400)

    allowed_methods = {"cash", "card", "mobile", "split"}
    payment_method = data.get("payment_method", "cash")
    if payment_method not in allowed_methods:
        return error_response(f"payment_method must be one of: {', '.join(allowed_methods)}", 400)

    customer = None
    customer_id = data.get("customer_id")
    if customer_id is not None:
        try:
            customer = Customer.query.get(int(customer_id))
        except (TypeError, ValueError):
            return error_response("customer_id must be an integer", 400)
        if not customer or not customer.is_active:
            return error_response("Customer not found", 404)

    total_amount = Decimal("0")
    sale_items = []

    for entry in items_data:
        product_id = entry.get("product_id")
        quantity = entry.get("quantity")

        if not product_id or not quantity:
            return error_response("Each item needs 'product_id' and 'quantity'", 400)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return error_response("Item quantity must be a positive integer", 400)

        product = Product.query.get(product_id)
        if not product or not product.is_active:
            return error_response(f"Product {product_id} not found", 404)
        if product.quantity_in_stock < quantity:
            return error_response(
                f"Insufficient stock for '{product.name}' "
                f"(available: {product.quantity_in_stock})",
                400,
            )

        unit_price = Decimal(str(product.price))
        subtotal = unit_price * quantity
        total_amount += subtotal
        sale_items.append((product, quantity, unit_price, subtotal))

    try:
        manual_discount = Decimal(str(data.get("discount", 0) or 0))
    except Exception:
        return error_response("discount must be numeric", 400)
    if manual_discount < 0:
        return error_response("discount cannot be negative", 400)

    loyalty_discount = Decimal("0")
    loyalty_points_redeemed = 0
    if customer and customer.loyalty_points >= LOYALTY_POINTS_THRESHOLD:
        loyalty_discount = (total_amount * LOYALTY_DISCOUNT_RATE).quantize(Decimal("0.01"))
        loyalty_points_redeemed = LOYALTY_POINTS_THRESHOLD

    discount = manual_discount + loyalty_discount
    if discount > total_amount:
        discount = total_amount

    try:
        tax_rate = Decimal(str(data.get("tax_rate", DEFAULT_TAX_RATE)))
    except Exception:
        return error_response("tax_rate must be numeric", 400)
    if tax_rate < 0:
        return error_response("tax_rate cannot be negative", 400)

    taxable_amount = total_amount - discount
    tax_amount = taxable_amount * tax_rate
    grand_total = taxable_amount + tax_amount

    try:
        user_id = int(get_jwt_identity())
        sale_payment_method = payment_method if payment_method != "split" else "cash"
        sale = Sale(
            user_id=user_id,
            total_amount=grand_total,
            items_count=len(sale_items),
            payment_method=sale_payment_method,
        )
        db.session.add(sale)
        db.session.flush()  # populate sale.id before inserting items

        for product, quantity, unit_price, subtotal in sale_items:
            item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )
            db.session.add(item)
            product.quantity_in_stock -= quantity

        total_change = Decimal("0")
        payment_records = []
        if payment_method == "split":
            split_payments = data.get("payments")
            if not isinstance(split_payments, list) or not split_payments:
                db.session.rollback()
                return error_response("payments must be a non-empty list for split payment", 400)

            split_total = Decimal("0")
            cash_payment_idx = None
            for idx, p in enumerate(split_payments):
                method = p.get("method")
                if method not in {"cash", "card", "mobile", "paystack"}:
                    db.session.rollback()
                    return error_response("Each split payment method must be cash, card, mobile, or paystack", 400)
                try:
                    amount = Decimal(str(p.get("amount", 0)))
                except Exception:
                    db.session.rollback()
                    return error_response("Each split payment amount must be numeric", 400)
                if amount <= 0:
                    db.session.rollback()
                    return error_response("Each split payment amount must be greater than 0", 400)

                if method in {"card", "mobile", "paystack"}:
                    verified, message = _verify_paystack_reference(str(p.get("reference") or ""), amount)
                    if not verified:
                        db.session.rollback()
                        return error_response(f"Split {method} verification failed: {message}", 400)

                split_total += amount
                if method == "cash" and cash_payment_idx is None:
                    cash_payment_idx = idx
                payment_records.append(
                    {
                        "method": "card" if method == "paystack" else method,
                        "amount": amount,
                        "reference": p.get("reference"),
                        "tendered_amount": p.get("tendered_amount"),
                        "change_amount": Decimal("0"),
                    }
                )

            if split_total < grand_total:
                db.session.rollback()
                return error_response("Split payment amount is less than total due", 400)
            over_paid = split_total - grand_total
            if over_paid > 0:
                if cash_payment_idx is None:
                    db.session.rollback()
                    return error_response("Overpayment in split mode requires a cash component for change", 400)
                payment_records[cash_payment_idx]["change_amount"] = over_paid
                total_change = over_paid
        else:
            paid_amount = grand_total
            tendered_amount = None
            payment_reference = data.get("payment_reference")
            if payment_method == "cash":
                raw_tendered = data.get("amount_tendered")
                if raw_tendered is not None:
                    try:
                        tendered_amount = Decimal(str(raw_tendered))
                    except Exception:
                        db.session.rollback()
                        return error_response("amount_tendered must be numeric", 400)
                    if tendered_amount < grand_total:
                        db.session.rollback()
                        return error_response("amount_tendered is less than total due", 400)
                    paid_amount = tendered_amount
                    total_change = tendered_amount - grand_total
            elif payment_method in {"card", "mobile"}:
                verified, message = _verify_paystack_reference(str(payment_reference or ""), grand_total)
                if not verified:
                    db.session.rollback()
                    return error_response(f"{payment_method} verification failed: {message}", 400)

            payment_records.append(
                {
                    "method": payment_method,
                    "amount": paid_amount,
                    "reference": payment_reference,
                    "tendered_amount": tendered_amount,
                    "change_amount": total_change,
                }
            )

        for p in payment_records:
            db.session.add(
                Payment(
                    sale_id=sale.id,
                    amount=p["amount"],
                    payment_method=p["method"],
                    reference=p.get("reference"),
                    tendered_amount=p.get("tendered_amount"),
                    change_amount=p.get("change_amount") or Decimal("0"),
                    status="confirmed",
                )
            )

        if customer:
            db.session.add(SaleCustomer(sale_id=sale.id, customer_id=customer.id))
            if loyalty_points_redeemed:
                customer.loyalty_points = max(0, customer.loyalty_points - loyalty_points_redeemed)
            points_earned = int(grand_total // Decimal("100"))
            customer.loyalty_points += points_earned

        db.session.commit()
        payload = sale.to_dict(include_items=True)
        payload["payment_method"] = payment_method
        payload["financials"] = {
            "subtotal": float(total_amount),
            "manual_discount": float(manual_discount),
            "loyalty_discount": float(loyalty_discount),
            "discount": float(discount),
            "tax_rate": float(tax_rate),
            "tax_amount": float(tax_amount),
            "grand_total": float(grand_total),
            "change_amount": float(total_change),
        }
        if customer:
            payload["customer"] = customer.to_dict()
        return success_response(payload, "Sale created", 201)
    except Exception:
        db.session.rollback()
        raise


@sales_bp.route("", methods=["GET"])
@any_authenticated
def list_sales():
    """List sales with optional filters and pagination.

    Query params:
        ``page``, ``per_page``, ``user_id``, ``payment_method``,
        ``date_from`` (YYYY-MM-DD), ``date_to`` (YYYY-MM-DD).

    Returns:
        200: Paginated list of sales.
    """
    query = Sale.query

    if request.args.get("user_id"):
        try:
            query = query.filter_by(user_id=int(request.args["user_id"]))
        except (ValueError, TypeError):
            return error_response("user_id must be an integer", 400)

    if request.args.get("payment_method"):
        query = query.filter_by(payment_method=request.args["payment_method"])

    if request.args.get("date_from"):
        try:
            df = datetime.strptime(request.args["date_from"], "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            query = query.filter(Sale.created_at >= df)
        except ValueError:
            return error_response("date_from must be in YYYY-MM-DD format", 400)

    if request.args.get("date_to"):
        try:
            dt = datetime.strptime(request.args["date_to"], "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
            query = query.filter(Sale.created_at <= dt)
        except ValueError:
            return error_response("date_to must be in YYYY-MM-DD format", 400)

    query = query.order_by(Sale.created_at.desc())
    return success_response(paginate_query(query))


@sales_bp.route("/report/daily", methods=["GET"])
@manager_or_admin_required
def daily_report():
    """Return aggregated sales totals grouped by day.

    Query params:
        ``date_from`` (YYYY-MM-DD, default: today),
        ``date_to``   (YYYY-MM-DD, default: today).

    Returns:
        200: List of daily aggregates.
    """
    today = date.today().isoformat()
    date_from_str = request.args.get("date_from", today)
    date_to_str = request.args.get("date_to", today)

    try:
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
    except ValueError:
        return error_response("Dates must be in YYYY-MM-DD format", 400)

    rows = (
        db.session.query(
            func.date(Sale.created_at).label("sale_date"),
            func.count(Sale.id).label("total_transactions"),
            func.sum(Sale.total_amount).label("total_revenue"),
            func.sum(Sale.items_count).label("total_items"),
        )
        .filter(Sale.created_at.between(date_from, date_to))
        .group_by(func.date(Sale.created_at))
        .order_by(func.date(Sale.created_at).asc())
        .all()
    )

    report = [
        {
            "date": str(row.sale_date),
            "total_transactions": row.total_transactions,
            "total_revenue": float(row.total_revenue or 0),
            "total_items": row.total_items or 0,
        }
        for row in rows
    ]
    return success_response(report)


@sales_bp.route("/report/monthly", methods=["GET"])
@manager_or_admin_required
def monthly_report():
    """Return aggregated sales totals grouped by month.

    Query params:
        ``year`` (int, default: current year).

    Returns:
        200: List of monthly aggregates.
    """
    try:
        year = int(request.args.get("year", datetime.now(timezone.utc).year))
    except (ValueError, TypeError):
        return error_response("year must be an integer", 400)

    rows = (
        db.session.query(
            func.extract("year", Sale.created_at).label("year"),
            func.extract("month", Sale.created_at).label("month_num"),
            func.count(Sale.id).label("total_transactions"),
            func.sum(Sale.total_amount).label("total_revenue"),
            func.sum(Sale.items_count).label("total_items"),
        )
        .filter(func.extract("year", Sale.created_at) == year)
        .group_by(
            func.extract("year", Sale.created_at),
            func.extract("month", Sale.created_at),
        )
        .order_by(func.extract("month", Sale.created_at).asc())
        .all()
    )

    report = [
        {
            "month": f"{int(row.year):04d}-{int(row.month_num):02d}",
            "total_transactions": row.total_transactions,
            "total_revenue": float(row.total_revenue or 0),
            "total_items": row.total_items or 0,
        }
        for row in rows
    ]
    return success_response(report)


@sales_bp.route("/<int:sale_id>", methods=["GET"])
@any_authenticated
def get_sale(sale_id: int):
    """Get a single sale with its line items.

    Args:
        sale_id: The sale's primary key.

    Returns:
        200: Sale details including items.
        404: Sale not found.
    """
    sale = Sale.query.get(sale_id)
    if not sale:
        return error_response("Sale not found", 404)
    return success_response(sale.to_dict(include_items=True))
