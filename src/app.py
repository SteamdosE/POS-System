"""Flask application factory."""

import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import get_config
from database import db


def create_app(config=None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional config object to override the default. Useful for testing.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    cfg = config or get_config()
    app.config.from_object(cfg)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, cfg.LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Extensions
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))
    JWTManager(app)

    # Database
    init_db(app)

    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.users import users_bp
    from src.routes.products import products_bp
    from src.routes.sales import sales_bp
    from src.routes.payments import payments_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(payments_bp)

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.exception("Unhandled exception")
        return jsonify({"success": False, "message": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
