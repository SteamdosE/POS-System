"""Product category management endpoints."""

from flask import Blueprint, request

from src.db import db
from src.models.category import Category
from src.utils.auth import manager_or_admin_required
from src.utils.helpers import success_response, error_response

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@categories_bp.route("", methods=["GET"])
@manager_or_admin_required
def list_categories():
    """Get all product categories.

    Returns:
        200: List of categories.
    """
    categories = Category.query.all()
    return success_response(
        {"categories": [cat.to_dict() for cat in categories]},
    )


@categories_bp.route("", methods=["POST"])
@manager_or_admin_required
def create_category():
    """Create a new product category.

    Request JSON body::

        {
            "name": "string"
        }

    Returns:
        201: Category created.
        400: Validation error or duplicate.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    name = data.get("name")
    if not name:
        return error_response("Field 'name' is required", 400)

    name = name.strip()
    if not name:
        return error_response("Category name cannot be empty", 400)

    existing = Category.query.filter_by(name=name).first()
    if existing:
        return error_response(f"Category '{name}' already exists", 400)

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return success_response(category.to_dict(), "Category created", 201)


@categories_bp.route("/<int:category_id>", methods=["PUT"])
@manager_or_admin_required
def update_category(category_id: int):
    """Update a product category name.

    Args:
        category_id: The category's primary key.

    Request JSON body::

        {
            "name": "string"
        }

    Returns:
        200: Category updated.
        400: Validation error or duplicate.
        404: Category not found.
    """
    category = Category.query.get(category_id)
    if not category:
        return error_response("Category not found", 404)

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return error_response("Field 'name' is required", 400)

    name = name.strip()
    if not name:
        return error_response("Category name cannot be empty", 400)

    existing = Category.query.filter_by(name=name).first()
    if existing and existing.id != category_id:
        return error_response(f"Category '{name}' already exists", 400)

    category.name = name
    db.session.commit()
    return success_response(category.to_dict(), "Category updated")


@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@manager_or_admin_required
def delete_category(category_id: int):
    """Delete a product category.

    Args:
        category_id: The category's primary key.

    Returns:
        200: Deletion confirmation.
        404: Category not found.
    """
    category = Category.query.get(category_id)
    if not category:
        return error_response("Category not found", 404)

    db.session.delete(category)
    db.session.commit()
    return success_response(message="Category deleted")
