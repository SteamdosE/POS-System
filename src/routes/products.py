"""Product management endpoints (CRUD)."""

from flask import Blueprint, request

from src.database import db
from src.models.product import Product
from src.utils.auth import admin_required, any_authenticated
from src.utils.helpers import success_response, error_response, paginate_query

products_bp = Blueprint("products", __name__, url_prefix="/api/products")


@products_bp.route("", methods=["GET"])
@any_authenticated
def list_products():
    """List all products with optional filtering and pagination.

    Query params:
        ``page``, ``per_page``, ``category``, ``search`` (name/SKU substring).

    Returns:
        200: Paginated list of products.
    """
    query = Product.query.filter_by(is_active=True)

    category = request.args.get("category")
    if category:
        query = query.filter(Product.category == category)

    search = request.args.get("search")
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Product.name.ilike(like), Product.sku.ilike(like))
        )

    query = query.order_by(Product.name.asc())
    return success_response(paginate_query(query))


@products_bp.route("/<int:product_id>", methods=["GET"])
@any_authenticated
def get_product(product_id: int):
    """Get a single product by ID.

    Args:
        product_id: The product's primary key.

    Returns:
        200: Product details.
        404: Product not found.
    """
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return error_response("Product not found", 404)
    return success_response(product.to_dict())


@products_bp.route("", methods=["POST"])
@admin_required
def create_product():
    """Create a new product (admin only).

    Request JSON body::

        {
            "name": "string",
            "sku": "string",
            "price": float,
            "description": "string",       (optional)
            "quantity_in_stock": int,       (optional, default 0)
            "category": "string"            (optional)
        }

    Returns:
        201: Product created.
        400: Validation error.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    required = ("name", "sku", "price")
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}", 400)

    if Product.query.filter_by(sku=data["sku"]).first():
        return error_response("SKU already exists", 400)

    try:
        price = float(data["price"])
        if price < 0:
            raise ValueError
    except (ValueError, TypeError):
        return error_response("Price must be a non-negative number", 400)

    product = Product(
        name=data["name"],
        sku=data["sku"],
        price=price,
        description=data.get("description"),
        quantity_in_stock=int(data.get("quantity_in_stock", 0)),
        category=data.get("category"),
    )
    db.session.add(product)
    db.session.commit()
    return success_response(product.to_dict(), "Product created", 201)


@products_bp.route("/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id: int):
    """Update a product (admin only).

    Args:
        product_id: The product's primary key.

    Returns:
        200: Updated product.
        400: Validation error.
        404: Product not found.
    """
    product = Product.query.get(product_id)
    if not product:
        return error_response("Product not found", 404)

    data = request.get_json(silent=True) or {}

    if "name" in data:
        product.name = data["name"]
    if "description" in data:
        product.description = data["description"]
    if "category" in data:
        product.category = data["category"]
    if "quantity_in_stock" in data:
        try:
            product.quantity_in_stock = int(data["quantity_in_stock"])
        except (ValueError, TypeError):
            return error_response("quantity_in_stock must be an integer", 400)
    if "price" in data:
        try:
            price = float(data["price"])
            if price < 0:
                raise ValueError
            product.price = price
        except (ValueError, TypeError):
            return error_response("Price must be a non-negative number", 400)
    if "sku" in data:
        existing = Product.query.filter_by(sku=data["sku"]).first()
        if existing and existing.id != product_id:
            return error_response("SKU already exists", 400)
        product.sku = data["sku"]

    db.session.commit()
    return success_response(product.to_dict(), "Product updated")


@products_bp.route("/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id: int):
    """Soft-delete a product (admin only).

    Args:
        product_id: The product's primary key.

    Returns:
        200: Deletion confirmation.
        404: Product not found.
    """
    product = Product.query.get(product_id)
    if not product:
        return error_response("Product not found", 404)

    product.is_active = False
    db.session.commit()
    return success_response(message="Product deleted")
