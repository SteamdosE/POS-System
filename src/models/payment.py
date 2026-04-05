"""Payment SQLAlchemy model."""

from src.models.base import BaseModel
from src.db import db


class Payment(BaseModel):
    """Represents one payment record for a sale."""

    __tablename__ = "payments"

    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(
        db.Enum("cash", "card", "mobile", name="payment_record_method"),
        nullable=False,
    )
    reference = db.Column(db.String(120), nullable=True)
    tendered_amount = db.Column(db.Numeric(10, 2), nullable=True)
    change_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(
        db.Enum("pending", "confirmed", "failed", name="payment_status"),
        nullable=False,
        default="confirmed",
    )
    notes = db.Column(db.String(255), nullable=True)

    sale = db.relationship("Sale", back_populates="payments")

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["amount"] = float(self.amount)
        data["tendered_amount"] = float(self.tendered_amount) if self.tendered_amount is not None else None
        data["change_amount"] = float(self.change_amount)
        return data
