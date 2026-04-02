"""Authentication endpoints: register and login."""

from flask import Blueprint, request
from flask_jwt_extended import create_access_token

from src.db import db
from src.models.user import User
from src.utils.helpers import success_response, error_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user.

    Request JSON body::

        {
            "username": "string",
            "email": "string",
            "password": "string",
            "role": "admin|manager|cashier"  (optional, defaults to cashier)
        }

    Returns:
        201: User created successfully.
        400: Validation error or duplicate username/email.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    required = ("username", "email", "password")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}", 400)

    if User.query.filter_by(username=data["username"]).first():
        return error_response("Username already taken", 400)
    if User.query.filter_by(email=data["email"]).first():
        return error_response("Email already registered", 400)

    allowed_roles = {"admin", "manager", "cashier"}
    role = data.get("role", "cashier")
    if role not in allowed_roles:
        return error_response(f"Invalid role. Must be one of: {', '.join(allowed_roles)}", 400)

    user = User(username=data["username"], email=data["email"], role=role)
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=user.id)
    return success_response({"user": user.to_dict(), "access_token": token}, "User registered", 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT.

    Request JSON body::

        {"username": "string", "password": "string"}

    Returns:
        200: Login successful with access token.
        400: Missing fields.
        401: Invalid credentials.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return error_response("Username and password are required", 400)

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return error_response("Invalid username or password", 401)
    if not user.is_active:
        return error_response("Account is deactivated", 403)

    token = create_access_token(identity=str(user.id))
    return success_response({"user": user.to_dict(), "access_token": token}, "Login successful")
