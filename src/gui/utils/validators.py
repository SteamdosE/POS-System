"""
Input Validation Utilities for POS System GUI
"""
import re
from typing import Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, ""
    return False, "Invalid email format"

def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate phone number format"""
    phone = re.sub(r'\D', '', phone)
    if len(phone) >= 10:
        return True, ""
    return False, "Phone number must be at least 10 digits"

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letters"
    return True, ""

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format"""
    if not 3 <= len(username) <= 20:
        return False, "Username must be 3-20 characters long"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def validate_barcode(barcode: str) -> Tuple[bool, str]:
    """Validate barcode format"""
    if not barcode:
        return False, "Barcode cannot be empty"
    if not re.match(r'^[a-zA-Z0-9\-]*$', barcode):
        return False, "Invalid barcode format"
    return True, ""

def validate_price(price_str: str) -> Tuple[bool, str]:
    """Validate price is positive number"""
    try:
        price = float(price_str)
        if price < 0:
            return False, "Price cannot be negative"
        if price == 0:
            return False, "Price must be greater than 0"
        return True, ""
    except ValueError:
        return False, "Invalid price format"

def validate_quantity(qty_str: str) -> Tuple[bool, str]:
    """Validate quantity is positive integer"""
    try:
        qty = int(qty_str)
        if qty < 0:
            return False, "Quantity cannot be negative"
        return True, ""
    except ValueError:
        return False, "Invalid quantity format"