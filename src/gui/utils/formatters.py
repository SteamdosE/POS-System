"""
Data Formatting Utilities for POS System GUI
"""
from datetime import datetime
from typing import Union

from .. import config as gui_config

def _coerce_float(value: Union[int, float, str, None]) -> float:
    """Convert user/API numeric values to float safely."""
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return 0.0

    cleaned = str(value).replace(",", "").strip()
    # Remove current and known currency symbols/codes if present.
    tokens = {gui_config.CURRENCY_SYMBOL, gui_config.CURRENCY_CODE} | set(gui_config.SUPPORTED_CURRENCIES.values()) | set(gui_config.SUPPORTED_CURRENCIES.keys())
    for token in tokens:
        if token:
            cleaned = cleaned.replace(token, "")
    cleaned = cleaned.strip()
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return 0.0

def format_currency(amount: Union[int, float, str, None]) -> str:
    """Format amount using the current app currency symbol."""
    return f"{gui_config.CURRENCY_SYMBOL} {_coerce_float(amount):,.2f}"

def _coerce_datetime(value: Union[datetime, str, None]) -> datetime | None:
    """Convert API date/datetime values to datetime objects when possible."""
    if isinstance(value, datetime):
        return value
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    # Accept common backend timestamp formats and ISO variants.
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass

    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue

    return None


def format_date(date_obj: Union[datetime, str, None]) -> str:
    """Format date as readable string (02 Apr 2026)."""
    parsed = _coerce_datetime(date_obj)
    if not parsed:
        return str(date_obj or "")
    return parsed.strftime("%d %b %Y")

def format_datetime(dt_obj: Union[datetime, str, None]) -> str:
    """Format datetime as readable string (02 Apr 2026 14:30)."""
    parsed = _coerce_datetime(dt_obj)
    if not parsed:
        return str(dt_obj or "")
    return parsed.strftime("%d %b %Y %H:%M")

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
    return _coerce_float(text)

def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage"""
    return f"{value:.{decimals}f}%"

def format_large_number(number: int) -> str:
    """Format large numbers with commas"""
    return f"{number:,}"