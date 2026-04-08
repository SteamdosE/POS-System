"""Customer management endpoints."""

from flask import Blueprint, request
from sqlalchemy import func

from src.db import db
from src.models.customer import Customer, SaleCustomer
from src.models.sale import Sale
from src.utils.auth import any_authenticated, manager_or_admin_required
from src.utils.helpers import success_response, error_response, paginate_query

customers_bp = Blueprint("customers", __name__, url_prefix="/api/customers")


def _norm(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


@customers_bp.route("", methods=["GET"])
@any_authenticated
def list_customers():
    """List active customers with optional text search."""
    query = Customer.query.filter_by(is_active=True)
    search = request.args.get("search")
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            db.or_(
                Customer.name.ilike(like),
                Customer.phone_number.ilike(like),
                Customer.email.ilike(like),
            )
        )

    query = query.order_by(Customer.name.asc())
    return success_response(paginate_query(query))


@customers_bp.route("", methods=["POST"])
@manager_or_admin_required
def create_customer():
    """Create a new customer profile."""
    data = request.get_json(silent=True) or {}

    name = _norm(data.get("name"))
    if not name:
        return error_response("Field 'name' is required", 400)

    phone_number = _norm(data.get("phone_number"))
    email = _norm(data.get("email"))
    address = _norm(data.get("address"))

    if phone_number and Customer.query.filter(func.lower(Customer.phone_number) == phone_number.lower()).first():
        return error_response("Phone number already exists", 400)
    if email and Customer.query.filter(func.lower(Customer.email) == email.lower()).first():
        return error_response("Email already exists", 400)

    customer = Customer(
        name=name,
        phone_number=phone_number,
        email=email,
        address=address,
        loyalty_points=int(data.get("loyalty_points") or 0),
    )
    db.session.add(customer)
    db.session.commit()
    return success_response(customer.to_dict(), "Customer created", 201)


@customers_bp.route("/<int:customer_id>", methods=["GET"])
@any_authenticated
def get_customer(customer_id: int):
    """Get a customer profile by ID."""
    customer = Customer.query.get(customer_id)
    if not customer or not customer.is_active:
        return error_response("Customer not found", 404)
    return success_response(customer.to_dict())


@customers_bp.route("/<int:customer_id>", methods=["PUT"])
@manager_or_admin_required
def update_customer(customer_id: int):
    """Update an existing customer profile."""
    customer = Customer.query.get(customer_id)
    if not customer or not customer.is_active:
        return error_response("Customer not found", 404)

    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = _norm(data.get("name"))
        if not name:
            return error_response("Field 'name' cannot be empty", 400)
        customer.name = name

    if "phone_number" in data:
        phone_number = _norm(data.get("phone_number"))
        if phone_number:
            existing = Customer.query.filter(
                func.lower(Customer.phone_number) == phone_number.lower(),
                Customer.id != customer.id,
            ).first()
            if existing:
                return error_response("Phone number already exists", 400)
        customer.phone_number = phone_number

    if "email" in data:
        email = _norm(data.get("email"))
        if email:
            existing = Customer.query.filter(
                func.lower(Customer.email) == email.lower(),
                Customer.id != customer.id,
            ).first()
            if existing:
                return error_response("Email already exists", 400)
        customer.email = email

    if "address" in data:
        customer.address = _norm(data.get("address"))

    if "loyalty_points" in data:
        try:
            points = int(data.get("loyalty_points"))
            if points < 0:
                raise ValueError
        except (TypeError, ValueError):
            return error_response("loyalty_points must be a non-negative integer", 400)
        customer.loyalty_points = points

    db.session.commit()
    return success_response(customer.to_dict(), "Customer updated")


@customers_bp.route("/<int:customer_id>", methods=["DELETE"])
@manager_or_admin_required
def delete_customer(customer_id: int):
    """Soft-delete a customer profile."""
    customer = Customer.query.get(customer_id)
    if not customer or not customer.is_active:
        return error_response("Customer not found", 404)

    customer.is_active = False
    db.session.commit()
    return success_response(message="Customer deleted")


@customers_bp.route("/<int:customer_id>/history", methods=["GET"])
@any_authenticated
def customer_purchase_history(customer_id: int):
    """Get customer purchase history and totals."""
    customer = Customer.query.get(customer_id)
    if not customer or not customer.is_active:
        return error_response("Customer not found", 404)

    links = (
        SaleCustomer.query.filter_by(customer_id=customer.id)
        .order_by(SaleCustomer.id.desc())
        .all()
    )

    sale_ids = [link.sale_id for link in links]
    sales = []
    total_spent = 0.0
    if sale_ids:
        sale_rows = (
            Sale.query.filter(Sale.id.in_(sale_ids))
            .order_by(Sale.created_at.desc())
            .all()
        )
        sales = [sale.to_dict(include_items=True) for sale in sale_rows]
        total_spent = sum(float(sale.total_amount) for sale in sale_rows)

    return success_response(
        {
            "customer": customer.to_dict(),
            "purchase_history": sales,
            "summary": {
                "total_orders": len(sales),
                "total_spent": total_spent,
                "loyalty_points": customer.loyalty_points,
            },
        }
    )
