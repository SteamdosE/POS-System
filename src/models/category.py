"""Category SQLAlchemy model."""

from src.models.base import BaseModel
from src.db import db


class Category(BaseModel):
    """Represents a product category."""

    __tablename__ = "categories"

    name = db.Column(db.String(80), nullable=False, unique=True, index=True)

    def __repr__(self) -> str:
        return f"<Category {self.name}>"
