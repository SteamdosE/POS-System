"""
GUI Configuration for POS System
Contains all settings, colors, fonts, and constants
"""

import json
import os

# API Configuration
API_BASE_URL = "http://localhost:5000/api"
API_TIMEOUT = 10

# Tax Configuration
TAX_RATE = 0.10  # 10%

# Colors
COLOR_PRIMARY = "#2E86AB"      # Professional Blue
COLOR_SECONDARY = "#A23B72"    # Purple
COLOR_SUCCESS = "#06A77D"      # Green
COLOR_WARNING = "#F77F00"      # Orange
COLOR_DANGER = "#D62828"       # Red
COLOR_LIGHT = "#F5F5F5"        # Light Gray
COLOR_DARK = "#333333"         # Dark Gray
COLOR_BORDER = "#CCCCCC"       # Border Gray
COLOR_WHITE = "#FFFFFF"        # White

# Fonts
FONT_TITLE = ("Helvetica", 16, "bold")
FONT_HEADING = ("Helvetica", 12, "bold")
FONT_NORMAL = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 9)
FONT_MONO = ("Courier", 10)

# Window Sizes
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Padding
PADDING_SMALL = 5
PADDING_MEDIUM = 10
PADDING_LARGE = 15
PADDING_XL = 20

# Messages
MSG_LOGIN_SUCCESS = "Login successful!"
MSG_LOGIN_FAILED = "Invalid username or password"
MSG_LOGOUT = "You have been logged out"
MSG_LOADING = "Loading..."
MSG_ERROR = "An error occurred"
MSG_SUCCESS = "Operation successful"
MSG_CONFIRM_DELETE = "Are you sure you want to delete this item?"
MSG_CONFIRM_LOGOUT = "Are you sure you want to logout?"

# Table Configuration
TABLE_HEIGHT = 15
TABLE_COLUMNS = 6

# Currency
CURRENCY_CODE = "GHS"
CURRENCY_SYMBOL = "GH₵"
DECIMAL_PLACES = 2

SUPPORTED_CURRENCIES = {
	"GHS": "GH₵",
	"KES": "Ksh",
	"USD": "$",
	"EUR": "€",
	"GBP": "£",
}

_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "app_settings.json")


def _load_app_settings() -> dict:
	"""Load persisted GUI settings from disk."""
	if not os.path.exists(_SETTINGS_FILE):
		return {}
	try:
		with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
			data = json.load(f)
			if isinstance(data, dict):
				return data
	except (OSError, ValueError, TypeError):
		pass
	return {}


def _save_app_settings(settings: dict) -> bool:
	"""Persist GUI settings to disk."""
	try:
		with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
			json.dump(settings, f, indent=2)
		return True
	except OSError:
		return False


def set_currency(currency_code: str) -> bool:
	"""Set current app currency and persist it."""
	global CURRENCY_CODE, CURRENCY_SYMBOL
	code = (currency_code or "").strip().upper()
	if code not in SUPPORTED_CURRENCIES:
		return False

	CURRENCY_CODE = code
	CURRENCY_SYMBOL = SUPPORTED_CURRENCIES[code]

	current = _load_app_settings()
	current["currency_code"] = CURRENCY_CODE
	return _save_app_settings(current)


def set_tax_rate(tax_rate: float) -> bool:
	"""Set current tax rate (e.g. 0.1 for 10%) and persist it."""
	global TAX_RATE
	try:
		rate = float(tax_rate)
	except (TypeError, ValueError):
		return False

	if rate < 0 or rate > 1:
		return False

	TAX_RATE = rate
	current = _load_app_settings()
	current["tax_rate"] = TAX_RATE
	return _save_app_settings(current)


def get_current_tax_rate() -> float:
	"""Return current tax rate value as fraction."""
	return TAX_RATE


def get_currency_display_options() -> list:
	"""Return currency options for dropdowns."""
	return [f"{code} ({symbol})" for code, symbol in SUPPORTED_CURRENCIES.items()]


def parse_currency_option(option: str) -> str:
	"""Extract currency code from option label like 'GHS (GH₵)'."""
	if not option:
		return ""
	return option.split(" ", 1)[0].strip().upper()


def get_current_currency_option() -> str:
	"""Return current currency as option label."""
	symbol = SUPPORTED_CURRENCIES.get(CURRENCY_CODE, CURRENCY_SYMBOL)
	return f"{CURRENCY_CODE} ({symbol})"


_loaded_settings = _load_app_settings()
_loaded_currency = str(_loaded_settings.get("currency_code", CURRENCY_CODE)).upper()
if _loaded_currency in SUPPORTED_CURRENCIES:
	CURRENCY_CODE = _loaded_currency
	CURRENCY_SYMBOL = SUPPORTED_CURRENCIES[_loaded_currency]

_loaded_tax = _loaded_settings.get("tax_rate", TAX_RATE)
try:
	_loaded_tax = float(_loaded_tax)
	if 0 <= _loaded_tax <= 1:
		TAX_RATE = _loaded_tax
except (TypeError, ValueError):
	pass