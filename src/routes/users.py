"""User management endpoints (CRUD)."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from src.db import db
from src.models.user import User
from src.utils.auth import admin_required, any_authenticated
from src.utils.helpers import success_response, error_response, paginate_query

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("", methods=["GET"])
@admin_required
def list_users():
    """List all users (admin only) with pagination.

    Query params: ``page``, ``per_page``.

    Returns:
        200: Paginated list of users.
    """
    query = User.query.order_by(User.created_at.desc())
    return success_response(paginate_query(query))


@users_bp.route("/<int:user_id>", methods=["GET"])
@any_authenticated
def get_user(user_id: int):
    """Get a single user by ID.

    A user may fetch their own profile; admins may fetch any user.

    Args:
        user_id: The target user's primary key.

    Returns:
        200: User details.
        403: Insufficient permissions.
        404: User not found.
    """
    current_id = get_jwt_identity()
    current_user = User.query.get(current_id)

    if current_user.role != "admin" and current_id != user_id:
        return error_response("Insufficient permissions", 403)

    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    return success_response(user.to_dict())


@users_bp.route("/<int:user_id>", methods=["PUT"])
@any_authenticated
def update_user(user_id: int):
    """Update a user record.

    Regular users may only update themselves. Admins may update any user.

    Args:
        user_id: The target user's primary key.

    Returns:
        200: Updated user details.
        400: Validation error.
        403: Insufficient permissions.
        404: User not found.
    """
    current_id = get_jwt_identity()
    current_user = User.query.get(current_id)

    if current_user.role != "admin" and current_id != user_id:
        return error_response("Insufficient permissions", 403)

    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}

    if "username" in data:
        existing = User.query.filter_by(username=data["username"]).first()
        if existing and existing.id != user_id:
            return error_response("Username already taken", 400)
        user.username = data["username"]

    if "email" in data:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            return error_response("Email already registered", 400)
        user.email = data["email"]

    if "password" in data and data["password"]:
        user.set_password(data["password"])

    # Only admins may change roles or active status
    if current_user.role == "admin":
        if "role" in data:
            allowed_roles = {"admin", "manager", "cashier"}
            if data["role"] not in allowed_roles:
                return error_response(f"Invalid role. Must be one of: {', '.join(allowed_roles)}", 400)
            user.role = data["role"]
        if "is_active" in data:
            user.is_active = bool(data["is_active"])

    db.session.commit()
    return success_response(user.to_dict(), "User updated")


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id: int):
    """Delete a user (admin only).

    Args:
        user_id: The target user's primary key.

    Returns:
        200: Deletion confirmation.
        404: User not found.
    """
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    db.session.delete(user)
    db.session.commit()
    return success_response(message="User deleted")
