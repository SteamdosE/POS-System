"""Payment record endpoints."""

from flask import Blueprint

from src.models.payment import Payment
from src.utils.auth import any_authenticated, manager_or_admin_required
from src.utils.helpers import success_response, error_response, paginate_query

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")


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
