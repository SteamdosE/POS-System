"""
Data Formatting Utilities for POS System GUI
"""
from datetime import datetime
from typing import Union

def _coerce_float(value: Union[int, float, str, None]) -> float:
    """Convert user/API numeric values to float safely."""
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return 0.0

    cleaned = str(value).replace("Ksh", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return 0.0

def format_currency(amount: Union[int, float, str, None]) -> str:
    """Format amount as currency (Ksh 1,234.50)"""
    return f"Ksh {_coerce_float(amount):,.2f}"

def format_date(date_obj: datetime) -> str:
    """Format date as readable string (02 Apr 2026)"""
    return date_obj.strftime("%d %b %Y")

def format_datetime(dt_obj: datetime) -> str:
    """Format datetime as readable string (02 Apr 2026 14:30)"""
    return dt_obj.strftime("%d %b %Y %H:%M")

def format_time(time_obj: datetime) -> str:
    """Format time as readable string (14:30)"""
    return time_obj.strftime("%H:%M")

def format_phone(phone: str) -> str:
    """Format phone number"""
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return phone

def parse_currency(text: str) -> float:
    """Convert currency string to float"""
    # Remove Ksh symbol and whitespace, convert to float
    return _coerce_float(text)

def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage"""
    return f"{value:.{decimals}f}%"

def format_large_number(number: int) -> str:
    """Format large numbers with commas"""
    return f"{number:,}"