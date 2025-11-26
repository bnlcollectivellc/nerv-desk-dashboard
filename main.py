#!/usr/bin/env python3
"""
NERV Dashboard for Inky Impression 5.7"
神経 - Evangelion-style desk display

Features:
- Large segmented LCD time display
- Date with Japanese labels
- Daylight arc visualization
- NERV/MAGI aesthetic elements
"""

import signal
import sys
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

from astral import LocationInfo
from astral.sun import sun

import config

# Try to import inky, fall back to preview mode if not available
try:
    from inky.inky_uc8159 import Inky as InkyImpression
    INKY_AVAILABLE = True
except ImportError:
    INKY_AVAILABLE = False
    print("Inky not available - running in preview mode")

# Try to import GPIO for button support
try:
    import gpiod
    from gpiod.line import Bias, Edge
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("GPIO not available - buttons disabled")

# Button GPIO pins (active low with pull-up)
BUTTONS = {
    "A": 5,
    "B": 6,
    "C": 16,
    "D": 24,
}


class NERVDashboard:
    """NERV-style dashboard renderer for Inky Impression."""

    def __init__(self):
        self.width = config.DISPLAY_WIDTH
        self.height = config.DISPLAY_HEIGHT
        self.colors = config.COLORS
        self.theme = config.THEME

        # Set up location for sun calculations
        loc = config.LOCATION
        self.location = LocationInfo(
            loc["name"],
            loc["region"],
            loc["timezone"],
            loc["latitude"],
            loc["longitude"]
        )

        # Initialize display if available
        # Inky Impression 5.7" uses UC8159 driver and needs manual init (no EEPROM)
        if INKY_AVAILABLE:
            self.display = InkyImpression(resolution=(self.width, self.height))
        else:
            self.display = None

        # Create base image
        self.image = Image.new("RGB", (self.width, self.height), self.colors["black"])
        self.draw = ImageDraw.Draw(self.image)

        # Load fonts (will use default if custom not available)
        self._load_fonts()

    def _load_fonts(self):
        """Load fonts for the display."""
        # Try to load a monospace font, fall back to default
        try:
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 72)
            self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 24)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
            self.font_jp = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except OSError:
            # Fall back to default font
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_jp = ImageFont.load_default()

    def _get_color(self, name):
        """Get RGB color tuple from theme name."""
        color_name = self.theme.get(name, name)
        return self.colors.get(color_name, self.colors["white"])

    def draw_hazard_stripes(self, x, y, width, height, stripe_width=10):
        """Draw diagonal hazard stripes (yellow/black)."""
        yellow = self._get_color("warning")
        black = self.colors["black"]

        # Draw yellow background
        self.draw.rectangle([x, y, x + width, y + height], fill=yellow)

        # Draw diagonal black stripes
        for i in range(-height, width + height, stripe_width * 2):
            points = [
                (x + i, y + height),
                (x + i + stripe_width, y + height),
                (x + i + height + stripe_width, y),
                (x + i + height, y),
            ]
            # Clip to bounds
            self.draw.polygon(points, fill=black)

    def draw_border_frame(self, x, y, width, height, thickness=2):
        """Draw NERV-style technical border."""
        color = self._get_color("primary")

        # Main rectangle
        self.draw.rectangle(
            [x, y, x + width, y + height],
            outline=color,
            width=thickness
        )

        # Corner accents (small squares)
        corner_size = 6
        corners = [
            (x, y),
            (x + width - corner_size, y),
            (x, y + height - corner_size),
            (x + width - corner_size, y + height - corner_size),
        ]
        for cx, cy in corners:
            self.draw.rectangle(
                [cx, cy, cx + corner_size, cy + corner_size],
                fill=color
            )

    def draw_segmented_digit(self, x, y, digit, size=60, thickness=8):
        """Draw a single 7-segment style digit."""
        color = self._get_color("primary")
        w = size // 2
        h = size
        t = thickness
        gap = 2

        # Segment definitions: (x1, y1, x2, y2) relative positions
        # Segments: top, top-right, bottom-right, bottom, bottom-left, top-left, middle
        segments = {
            'top':    [(gap, 0), (w - gap, 0), (w - gap - t//2, t), (gap + t//2, t)],
            'tr':     [(w - t, gap), (w, gap), (w, h//2 - gap), (w - t, h//2 - gap - t//2)],
            'br':     [(w - t, h//2 + gap + t//2), (w, h//2 + gap), (w, h - gap), (w - t, h - gap)],
            'bottom': [(gap + t//2, h - t), (w - gap - t//2, h - t), (w - gap, h), (gap, h)],
            'bl':     [(0, h//2 + gap), (t, h//2 + gap + t//2), (t, h - gap), (0, h - gap)],
            'tl':     [(0, gap), (t, gap), (t, h//2 - gap - t//2), (0, h//2 - gap)],
            'mid':    [(gap + t//2, h//2 - t//2), (w - gap - t//2, h//2 - t//2),
                       (w - gap - t//2, h//2 + t//2), (gap + t//2, h//2 + t//2)],
        }

        # Which segments are on for each digit
        digit_segments = {
            '0': ['top', 'tr', 'br', 'bottom', 'bl', 'tl'],
            '1': ['tr', 'br'],
            '2': ['top', 'tr', 'mid', 'bl', 'bottom'],
            '3': ['top', 'tr', 'mid', 'br', 'bottom'],
            '4': ['tl', 'mid', 'tr', 'br'],
            '5': ['top', 'tl', 'mid', 'br', 'bottom'],
            '6': ['top', 'tl', 'mid', 'bl', 'br', 'bottom'],
            '7': ['top', 'tr', 'br'],
            '8': ['top', 'tr', 'br', 'bottom', 'bl', 'tl', 'mid'],
            '9': ['top', 'tr', 'br', 'bottom', 'tl', 'mid'],
            ':': [],  # Special case for colon
        }

        if digit == ':':
            # Draw colon
            dot_size = t
            self.draw.ellipse([x + w//4, y + h//3 - dot_size//2,
                              x + w//4 + dot_size, y + h//3 + dot_size//2], fill=color)
            self.draw.ellipse([x + w//4, y + 2*h//3 - dot_size//2,
                              x + w//4 + dot_size, y + 2*h//3 + dot_size//2], fill=color)
            return w//2 + 5

        active_segments = digit_segments.get(str(digit), [])

        for seg_name in active_segments:
            points = [(x + px, y + py) for px, py in segments[seg_name]]
            self.draw.polygon(points, fill=color)

        return w + 10  # Return width for spacing

    def draw_time(self, x, y, current_time):
        """Draw large segmented time display."""
        time_str = current_time.strftime("%H:%M")

        # Draw Japanese label above
        self.draw.text((x, y - 25), config.LABELS["time"],
                       font=self.font_jp, fill=self._get_color("secondary"))

        # Draw each character
        offset_x = x
        for char in time_str:
            width = self.draw_segmented_digit(offset_x, y, char, size=80, thickness=10)
            offset_x += width

        # Draw seconds smaller below
        seconds = current_time.strftime(":%S")
        self.draw.text((offset_x + 10, y + 50), seconds,
                       font=self.font_medium, fill=self._get_color("primary"))

    def draw_date(self, x, y, current_time):
        """Draw date display."""
        # Japanese label
        self.draw.text((x, y), config.LABELS["date"],
                       font=self.font_jp, fill=self._get_color("secondary"))

        # Date in format: 2024.12.25 WED
        date_str = current_time.strftime("%Y.%m.%d")
        day_str = current_time.strftime("%a").upper()

        self.draw.text((x, y + 20), date_str,
                       font=self.font_medium, fill=self._get_color("primary"))
        self.draw.text((x + 150, y + 20), day_str,
                       font=self.font_medium, fill=self._get_color("accent"))

    def draw_daylight_arc(self, x, y, width, height, current_time):
        """Draw 24-hour sun arc: midnight to midnight with S-curves for night."""
        import math

        # Get sun times
        try:
            s = sun(self.location.observer, date=current_time.date(),
                   tzinfo=self.location.timezone)
            sunrise = s["sunrise"]
            sunset = s["sunset"]
            noon = s["noon"]
        except Exception as e:
            self.draw.text((x, y), f"Sun calc error: {e}",
                          font=self.font_small, fill=self._get_color("accent"))
            return

        # Draw label
        self.draw.text((x, y), config.LABELS["daylight"],
                       font=self.font_jp, fill=self._get_color("secondary"))

        arc_y = y + 25
        arc_height = height - 50  # Leave room for labels

        # Calculate time fractions (0-1 over 24 hours)
        # Use naive datetime for consistent math (astral returns timezone-aware)
        midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        sunrise_naive = sunrise.replace(tzinfo=None)
        sunset_naive = sunset.replace(tzinfo=None)
        midnight_naive = midnight if midnight.tzinfo is None else midnight.replace(tzinfo=None)
        current_naive = current_time if current_time.tzinfo is None else current_time.replace(tzinfo=None)

        sunrise_frac = (sunrise_naive - midnight_naive).total_seconds() / 86400
        sunset_frac = (sunset_naive - midnight_naive).total_seconds() / 86400

        # Horizon line Y position (middle of arc area)
        horizon_y = arc_y + arc_height // 2

        def get_sun_height(time_frac):
            """Calculate sun height: positive during day (arc), negative at night (S-curve)."""
            if sunrise_frac <= time_frac <= sunset_frac:
                # Daytime: parabolic arc above horizon
                # Normalize to 0-1 within daylight hours
                day_progress = (time_frac - sunrise_frac) / (sunset_frac - sunrise_frac)
                # Parabola peaking at solar noon
                return arc_height // 2 * math.sin(day_progress * math.pi)
            elif time_frac < sunrise_frac:
                # Before sunrise: S-curve rising from midnight
                # Progress from midnight (0) to sunrise
                night_progress = time_frac / sunrise_frac
                # S-curve using sine, staying below horizon
                return -arc_height // 4 * math.cos(night_progress * math.pi / 2)
            else:
                # After sunset: S-curve descending to midnight
                # Progress from sunset to midnight (1)
                night_progress = (time_frac - sunset_frac) / (1 - sunset_frac)
                # S-curve descending below horizon
                return -arc_height // 4 * math.sin(night_progress * math.pi / 2)

        # Draw the full 24-hour arc path
        arc_color = self._get_color("secondary")
        prev_point = None
        for i in range(width + 1):
            time_frac = i / width
            sun_h = get_sun_height(time_frac)
            point = (x + i, horizon_y - sun_h)
            if prev_point:
                self.draw.line([prev_point, point], fill=arc_color, width=2)
            prev_point = point

        # Draw horizon line
        self.draw.line([(x, horizon_y), (x + width, horizon_y)],
                      fill=self._get_color("primary"), width=1)

        # Draw sunrise vertical line
        sunrise_x = x + int(sunrise_frac * width)
        self.draw.line([(sunrise_x, arc_y), (sunrise_x, horizon_y + arc_height // 4)],
                      fill=self._get_color("warning"), width=1)
        # Sunrise time to the LEFT of the line
        sunrise_str = sunrise.strftime("%H:%M")
        self.draw.text((sunrise_x - 45, horizon_y + arc_height // 4 + 2), sunrise_str,
                       font=self.font_small, fill=self._get_color("warning"))

        # Draw sunset vertical line
        sunset_x = x + int(sunset_frac * width)
        self.draw.line([(sunset_x, arc_y), (sunset_x, horizon_y + arc_height // 4)],
                      fill=self._get_color("accent"), width=1)
        # Sunset time to the RIGHT of the line
        sunset_str = sunset.strftime("%H:%M")
        self.draw.text((sunset_x + 5, horizon_y + arc_height // 4 + 2), sunset_str,
                       font=self.font_small, fill=self._get_color("accent"))

        # Calculate current sun position
        now_frac = (current_naive - midnight_naive).total_seconds() / 86400
        sun_h = get_sun_height(now_frac)
        sun_x = x + int(now_frac * width)
        sun_y = int(horizon_y - sun_h)

        # Sun color: yellow during day, red at night
        is_day = sunrise_frac <= now_frac <= sunset_frac
        sun_color = self._get_color("warning") if is_day else self._get_color("accent")
        sun_radius = 8
        self.draw.ellipse([sun_x - sun_radius, sun_y - sun_radius,
                          sun_x + sun_radius, sun_y + sun_radius],
                         fill=sun_color)

    def draw_nerv_header(self):
        """Draw NERV-style header with hazard stripes."""
        # Top hazard stripe
        self.draw_hazard_stripes(0, 0, self.width, 15)

        # NERV logo area
        self.draw.text((20, 20), "NERV", font=self.font_medium,
                       fill=self._get_color("accent"))
        self.draw.text((85, 25), "DESK TERMINAL", font=self.font_small,
                       fill=self._get_color("primary"))

        # System status indicator
        self.draw.text((self.width - 150, 20), config.LABELS["system"],
                       font=self.font_jp, fill=self._get_color("secondary"))
        self.draw.text((self.width - 150, 38), config.LABELS["active"],
                       font=self.font_small, fill=self._get_color("secondary"))

        # Status light
        self.draw.ellipse([self.width - 30, 25, self.width - 15, 40],
                         fill=self._get_color("secondary"))

    def draw_magi_status(self, x, y):
        """Draw MAGI system status display."""
        magi_systems = ["MELCHIOR-1", "BALTHASAR-2", "CASPER-3"]

        self.draw.text((x, y), config.LABELS["magi"],
                       font=self.font_small, fill=self._get_color("accent"))

        for i, name in enumerate(magi_systems):
            sys_y = y + 20 + (i * 18)
            # Status bar
            self.draw.rectangle([x, sys_y, x + 100, sys_y + 12],
                               outline=self._get_color("primary"), width=1)
            # Fill (simulated load)
            fill_width = 70 + (i * 10)  # Vary the "load"
            self.draw.rectangle([x + 2, sys_y + 2, x + fill_width, sys_y + 10],
                               fill=self._get_color("secondary"))
            # Label
            self.draw.text((x + 105, sys_y - 2), name,
                          font=self.font_small, fill=self._get_color("secondary"))

    def render(self):
        """Render the complete dashboard."""
        # Clear image
        self.draw.rectangle([0, 0, self.width, self.height],
                           fill=self.colors["black"])

        now = datetime.now()

        # Draw components
        self.draw_nerv_header()

        # Main time display (centered, large)
        self.draw_time(40, 70, now)

        # Date display
        self.draw_date(40, 190, now)

        # Technical border around main display area
        self.draw_border_frame(30, 55, 350, 190, thickness=2)

        # Daylight arc
        self.draw_daylight_arc(30, 260, 350, 100, now)
        self.draw_border_frame(30, 255, 350, 110, thickness=2)

        # MAGI status (right side)
        self.draw_magi_status(420, 70)
        self.draw_border_frame(410, 55, 175, 100, thickness=2)

        # Bottom hazard stripe
        self.draw_hazard_stripes(0, self.height - 15, self.width, 15)

        # Bottom status text
        self.draw.text((20, self.height - 40),
                      "PRIORITY: NORMAL  |  SYNC RATE: 100%  |  AT FIELD: STABLE",
                      font=self.font_small, fill=self._get_color("secondary"))

        return self.image

    def update_display(self):
        """Update the Inky display with current render."""
        image = self.render()

        if self.display:
            self.display.set_image(image)
            self.display.show()
            print(f"Display updated at {datetime.now().strftime('%H:%M:%S')}")
        else:
            # Save preview image
            image.save("preview.png")
            print(f"Preview saved to preview.png at {datetime.now().strftime('%H:%M:%S')}")

    def setup_buttons(self):
        """Set up GPIO button handlers."""
        if not GPIO_AVAILABLE:
            return None

        try:
            chip = gpiod.Chip("/dev/gpiochip4")  # Pi 5 uses gpiochip4
        except FileNotFoundError:
            try:
                chip = gpiod.Chip("/dev/gpiochip0")  # Older Pi uses gpiochip0
            except FileNotFoundError:
                print("No GPIO chip found - buttons disabled")
                return None

        # Request button B line for edge detection
        line_config = gpiod.LineSettings(
            edge_detection=Edge.FALLING,
            bias=Bias.PULL_UP,
            debounce_period=timedelta(milliseconds=100)
        )

        try:
            self.button_request = chip.request_lines(
                consumer="nerv-dashboard",
                config={BUTTONS["B"]: line_config}
            )
            print(f"Button B (GPIO {BUTTONS['B']}) ready - press for force refresh")
            return self.button_request
        except Exception as e:
            print(f"Could not set up buttons: {e}")
            return None

    def check_buttons(self):
        """Check if button B was pressed."""
        if not hasattr(self, 'button_request') or self.button_request is None:
            return False

        # Check for edge events (non-blocking)
        if self.button_request.wait_edge_events(timeout=0):
            events = self.button_request.read_edge_events()
            for event in events:
                if event.line_offset == BUTTONS["B"]:
                    print("Button B pressed - force refresh!")
                    return True
        return False

    def run(self):
        """Main loop - update display periodically."""
        print("NERV Dashboard starting...")
        print(f"Location: {self.location.name}, {self.location.region}")
        print(f"Update interval: {config.UPDATE_INTERVAL} seconds")
        print("-" * 40)

        # Set up button handlers
        self.setup_buttons()

        # Initial update
        self.update_display()

        try:
            while True:
                # Check for button press every 0.5 seconds
                for _ in range(config.UPDATE_INTERVAL * 2):
                    if self.check_buttons():
                        self.update_display()
                        break
                    time.sleep(0.5)
                else:
                    # No button press - do scheduled update
                    self.update_display()
        except KeyboardInterrupt:
            print("\nDashboard stopped.")
            sys.exit(0)


if __name__ == "__main__":
    dashboard = NERVDashboard()

    # Check for single-run mode
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        dashboard.update_display()
    else:
        dashboard.run()
