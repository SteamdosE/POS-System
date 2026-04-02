"""User SQLAlchemy model."""

from werkzeug.security import generate_password_hash, check_password_hash
from src.models.base import BaseModel
from src.database import db


class User(BaseModel):
    """Represents a system user (admin, manager, or cashier)."""

    __tablename__ = "users"

    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(
        db.Enum("admin", "manager", "cashier", name="user_role"),
        nullable=False,
        default="cashier",
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    sales = db.relationship("Sale", back_populates="cashier", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Hash and store the user's password.

        Args:
            password: Plain-text password.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plain-text password against the stored hash.

        Args:
            password: Plain-text password to verify.

        Returns:
            bool: True if the password matches.
        """
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Serialize the user, excluding the password hash.

        Returns:
            dict: User fields safe for API responses.
        """
        data = super().to_dict()
        data.pop("password_hash", None)
        return data

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
