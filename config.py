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
