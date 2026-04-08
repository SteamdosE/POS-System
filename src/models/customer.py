"""Customer and customer-sale link SQLAlchemy models."""

from src.models.base import BaseModel
from src.db import db


class Customer(BaseModel):
    """Represents a customer profile and loyalty balance."""

    __tablename__ = "customers"

    name = db.Column(db.String(120), nullable=False, index=True)
    phone_number = db.Column(db.String(30), nullable=True, unique=True, index=True)
    email = db.Column(db.String(120), nullable=True, unique=True, index=True)
    address = db.Column(db.String(255), nullable=True)
    loyalty_points = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    sales_links = db.relationship(
        "SaleCustomer",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Customer {self.id}: {self.name}>"


class SaleCustomer(db.Model):
    """Maps a sale to a customer for purchase history tracking."""

    __tablename__ = "sale_customers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False, unique=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)

    sale = db.relationship("Sale")
    customer = db.relationship("Customer", back_populates="sales_links")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "customer_id": self.customer_id,
        }