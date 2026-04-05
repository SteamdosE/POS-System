"""Models package – exports all SQLAlchemy model classes."""

from src.models.base import BaseModel
from src.models.user import User
from src.models.product import Product
from src.models.category import Category
from src.models.sale import Sale, SaleItem

__all__ = ["BaseModel", "User", "Product", "Category", "Sale", "SaleItem"]
