"""SQLAlchemy database instance and initialization helpers."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()


def init_db(app) -> None:
    """Initialize the database with the Flask app.

    Args:
        app: The Flask application instance.
    """
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        # Import models so SQLAlchemy registers them before creating tables
        from src.models import User, Product, Sale, SaleItem  # noqa: F401
        db.create_all()
