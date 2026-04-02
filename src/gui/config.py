"""
GUI Configuration for POS System
Contains all settings, colors, fonts, and constants
"""

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
CURRENCY_SYMBOL = "Ksh"
DECIMAL_PLACES = 2