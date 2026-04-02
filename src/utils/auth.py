"""JWT authentication and authorization helpers."""

from functools import wraps
from typing import Callable

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from src.models.user import User


def _get_current_user() -> User | None:
    """Return the User object for the currently authenticated JWT identity.

    Returns:
        User | None: The authenticated user, or None if not found.
    """
    user_id = get_jwt_identity()
    return User.query.get(user_id)


def jwt_required_with_roles(*roles: str) -> Callable:
    """Decorator factory that enforces JWT authentication and optional role checks.

    Args:
        *roles: Allowed role strings. If empty, any authenticated user is permitted.

    Returns:
        Callable: A decorator that wraps the view function.

    Example::

        @jwt_required_with_roles("admin", "manager")
        def admin_only_view():
            ...
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _get_current_user()
            if user is None:
                return jsonify({"error": "User not found"}), 401
            if not user.is_active:
                return jsonify({"error": "Account is deactivated"}), 403
            if roles and user.role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(fn: Callable) -> Callable:
    """Shorthand decorator: requires the 'admin' role."""
    return jwt_required_with_roles("admin")(fn)


def manager_or_admin_required(fn: Callable) -> Callable:
    """Shorthand decorator: requires 'admin' or 'manager' role."""
    return jwt_required_with_roles("admin", "manager")(fn)


def any_authenticated(fn: Callable) -> Callable:
    """Shorthand decorator: requires a valid JWT but no specific role."""
    return jwt_required_with_roles()(fn)
