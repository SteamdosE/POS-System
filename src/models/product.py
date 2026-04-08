"""Product SQLAlchemy model."""

from src.models.base import BaseModel
from src.db import db


class Product(BaseModel):
    """Represents a product available for sale."""

    __tablename__ = "products"

    name = db.Column(db.String(120), nullable=False, index=True)
    sku = db.Column(db.String(64), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity_in_stock = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(80), nullable=True, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    sale_items = db.relationship("SaleItem", back_populates="product", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Product {self.sku}: {self.name}>"
