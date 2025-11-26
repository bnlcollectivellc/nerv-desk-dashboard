"""
NERV Dashboard Configuration
活動限界 - Configuration Parameters
"""

# Display settings
DISPLAY_WIDTH = 600
DISPLAY_HEIGHT = 448

# Location: Hacienda Heights, CA
LOCATION = {
    "name": "Hacienda Heights",
    "region": "California",
    "timezone": "America/Los_Angeles",
    "latitude": 33.9931,
    "longitude": -117.9687,
}

# NERV Color Palette (7-color e-paper compatible)
# Inky Impression supports: BLACK, WHITE, RED, YELLOW, ORANGE, BLUE, GREEN
COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "yellow": (255, 255, 0),
    "orange": (255, 128, 0),
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
}

# UI Theme
THEME = {
    "background": "black",
    "primary": "orange",      # Main text, borders
    "secondary": "green",     # Data, secondary text
    "accent": "red",          # Warnings, highlights
    "warning": "yellow",      # Hazard stripes
}

# Update interval (seconds)
UPDATE_INTERVAL = 300  # 5 minutes

# Pages configuration
PAGES = ["dashboard", "todos", "experimental"]
DEFAULT_PAGE = "dashboard"

# Button mapping (active low, accent on press)
# A = prev page, B = next page, C = special action, D = refresh
BUTTONS = {
    "A": 5,   # Previous page
    "B": 6,   # Next page
    "C": 16,  # Special/page-specific action
    "D": 24,  # Force refresh
}

# Calendar (iCloud ICS)
# To get your calendar URL:
# 1. Open Calendar app on Mac
# 2. Right-click your calendar -> Share Calendar
# 3. Check "Public Calendar" and copy the URL
CALENDAR_ICS_URL = ""  # Paste your webcal:// or https:// URL here
CALENDAR_CACHE_MINUTES = 15

# Notion Integration
# Setup:
# 1. Go to notion.so/my-integrations
# 2. Create new integration, copy the API key
# 3. Share your database with the integration
# 4. Copy the database ID from the URL
NOTION_API_KEY = ""
NOTION_DATABASE_ID = ""

# Japanese labels
LABELS = {
    "time": "現在時刻",           # Current Time
    "date": "日付",              # Date
    "daylight": "日照状況",       # Daylight Status
    "sunrise": "日出",           # Sunrise
    "sunset": "日没",            # Sunset
    "system": "システム状態",     # System Status
    "active": "活動中",          # Active
    "nerv": "NERV",
    "magi": "MAGI",
}
