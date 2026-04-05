"""SQLAlchemy database instance and initialization helpers."""

import sqlite3

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine

db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key enforcement for every new SQLite connection."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db(app) -> None:
    """Initialize the database with the Flask app.

    Args:
        app: The Flask application instance.
    """
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        # Import models so SQLAlchemy registers them before creating tables
        from src.models import User, Product, Sale, SaleItem, Category, Customer, SaleCustomer, Payment  # noqa: F401
        db.create_all()
