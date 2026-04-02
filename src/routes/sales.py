"""Sales endpoints: checkout, listing, and reporting."""

from datetime import datetime, timezone, date
from decimal import Decimal

from flask import Blueprint, request
from sqlalchemy import func

from src.database import db
from src.models.product import Product
from src.models.sale import Sale, SaleItem
from src.utils.auth import any_authenticated, manager_or_admin_required
from src.utils.helpers import success_response, error_response, paginate_query
from flask_jwt_extended import get_jwt_identity

sales_bp = Blueprint("sales", __name__, url_prefix="/api/sales")


@sales_bp.route("", methods=["POST"])
@any_authenticated
def create_sale():
    """Process a new sale / checkout.

    Request JSON body::

        {
            "payment_method": "cash|card|mobile",
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

    allowed_methods = {"cash", "card", "mobile"}
    payment_method = data.get("payment_method", "cash")
    if payment_method not in allowed_methods:
        return error_response(f"payment_method must be one of: {', '.join(allowed_methods)}", 400)

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

    user_id = get_jwt_identity()
    sale = Sale(
        user_id=user_id,
        total_amount=total_amount,
        items_count=len(sale_items),
        payment_method=payment_method,
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

    db.session.commit()
    return success_response(sale.to_dict(include_items=True), "Sale created", 201)


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
