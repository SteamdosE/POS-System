"""Sale and SaleItem SQLAlchemy models."""

from datetime import datetime, timezone
from src.db import db
from src.models.base import BaseModel


class Sale(db.Model):
    """Represents a completed sales transaction."""

    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    items_count = db.Column(db.Integer, nullable=False, default=0)
    payment_method = db.Column(
        db.Enum("cash", "card", "mobile", name="payment_method"),
        nullable=False,
        default="cash",
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    cashier = db.relationship("User", back_populates="sales")
    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    def to_dict(self, include_items: bool = False) -> dict:
        """Serialize the sale to a dictionary.

        Args:
            include_items: When True, embed the list of sale items.

        Returns:
            dict: Sale fields for API responses.
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "total_amount": float(self.total_amount),
            "items_count": self.items_count,
            "payment_method": self.payment_method,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data

    def __repr__(self) -> str:
        return f"<Sale {self.id} total={self.total_amount}>"


class SaleItem(db.Model):
    """Represents a single line item within a sale."""

    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False, index=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationships
    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product", back_populates="sale_items")

    def to_dict(self) -> dict:
        """Serialize the sale item.

        Returns:
            dict: SaleItem fields for API responses.
        """
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "subtotal": float(self.subtotal),
        }

    def __repr__(self) -> str:
        return f"<SaleItem sale={self.sale_id} product={self.product_id} qty={self.quantity}>"
