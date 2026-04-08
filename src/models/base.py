"""Base SQLAlchemy model with common fields."""

from datetime import datetime, timezone
from src.db import db


class BaseModel(db.Model):
    """Abstract base model providing id and timestamp fields."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Serialize the model instance to a dictionary.

        Returns:
            dict: Column name -> value mapping.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def save(self) -> "BaseModel":
        """Persist the model instance to the database.

        Returns:
            BaseModel: The saved instance.
        """
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> None:
        """Remove the model instance from the database."""
        db.session.delete(self)
        db.session.commit()
