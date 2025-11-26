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
        """Draw daylight arc showing sun position between sunrise and sunset."""
        # Get sun times
        try:
            s = sun(self.location.observer, date=current_time.date(),
                   tzinfo=self.location.timezone)
            sunrise = s["sunrise"]
            sunset = s["sunset"]
        except Exception as e:
            # Fallback if sun calculation fails
            self.draw.text((x, y), f"Sun calc error: {e}",
                          font=self.font_small, fill=self._get_color("accent"))
            return

        # Draw label
        self.draw.text((x, y), config.LABELS["daylight"],
                       font=self.font_jp, fill=self._get_color("secondary"))

        arc_y = y + 25
        arc_height = height - 40

        # Draw arc background (the path)
        arc_color = self._get_color("secondary")
        arc_points = []
        for i in range(width + 1):
            # Parabolic arc
            progress = i / width
            arc_offset = -4 * arc_height * (progress - 0.5) ** 2 + arc_height
            arc_points.append((x + i, arc_y + arc_height - arc_offset))

        # Draw arc line
        for i in range(len(arc_points) - 1):
            self.draw.line([arc_points[i], arc_points[i + 1]],
                          fill=arc_color, width=2)

        # Draw horizon line
        horizon_y = arc_y + arc_height
        self.draw.line([(x, horizon_y), (x + width, horizon_y)],
                      fill=self._get_color("primary"), width=1)

        # Calculate sun position
        now_ts = current_time.timestamp()
        sunrise_ts = sunrise.timestamp()
        sunset_ts = sunset.timestamp()

        if now_ts < sunrise_ts:
            # Before sunrise
            sun_progress = 0
            is_day = False
        elif now_ts > sunset_ts:
            # After sunset
            sun_progress = 1
            is_day = False
        else:
            # During day
            sun_progress = (now_ts - sunrise_ts) / (sunset_ts - sunrise_ts)
            is_day = True

        # Draw sun position
        sun_x = x + int(sun_progress * width)
        sun_arc_offset = -4 * arc_height * (sun_progress - 0.5) ** 2 + arc_height
        sun_y = int(arc_y + arc_height - sun_arc_offset)

        sun_color = self._get_color("warning") if is_day else self._get_color("accent")
        sun_radius = 8
        self.draw.ellipse([sun_x - sun_radius, sun_y - sun_radius,
                          sun_x + sun_radius, sun_y + sun_radius],
                         fill=sun_color)

        # Draw sunrise/sunset times
        sunrise_str = sunrise.strftime("%H:%M")
        sunset_str = sunset.strftime("%H:%M")

        self.draw.text((x, horizon_y + 5), f"{config.LABELS['sunrise']} {sunrise_str}",
                       font=self.font_small, fill=self._get_color("secondary"))
        self.draw.text((x + width - 80, horizon_y + 5), f"{config.LABELS['sunset']} {sunset_str}",
                       font=self.font_small, fill=self._get_color("secondary"))

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
