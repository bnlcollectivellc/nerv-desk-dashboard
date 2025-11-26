"""
Dashboard Page - Main display
Time, date, daylight arc, upcoming events
"""

import math
from datetime import datetime, timedelta
from PIL import ImageDraw

from astral import LocationInfo
from astral.sun import sun

import config
from pages.base import Page


class DashboardPage(Page):
    """Main dashboard with time, date, sun arc, and events."""

    name = "dashboard"
    title = "MAIN TERMINAL"
    title_jp = "メイン端末"

    def __init__(self, width, height, fonts):
        super().__init__(width, height, fonts)

        # Set up location for sun calculations
        loc = config.LOCATION
        self.location = LocationInfo(
            loc["name"],
            loc["region"],
            loc["timezone"],
            loc["latitude"],
            loc["longitude"]
        )

        # Calendar events
        self.events = []
        self._last_fetch = None

    def refresh_events(self):
        """Fetch fresh calendar events."""
        try:
            from integrations.calendar import get_calendar_events
            self.events = get_calendar_events(max_events=6)
            self._last_fetch = datetime.now()
            print(f"Fetched {len(self.events)} calendar events")
        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            self.events = []

    def draw_segmented_digit(self, draw, x, y, digit, size=80, thickness=10):
        """Draw a single 7-segment style digit."""
        color = self._get_color("primary")
        w = size // 2
        h = size
        t = thickness
        gap = 2

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
            ':': [],
        }

        if digit == ':':
            dot_size = t
            draw.ellipse([x + w//4, y + h//3 - dot_size//2,
                         x + w//4 + dot_size, y + h//3 + dot_size//2], fill=color)
            draw.ellipse([x + w//4, y + 2*h//3 - dot_size//2,
                         x + w//4 + dot_size, y + 2*h//3 + dot_size//2], fill=color)
            return w//2 + 8

        active = digit_segments.get(str(digit), [])
        for seg_name in active:
            points = [(x + px, y + py) for px, py in segments[seg_name]]
            draw.polygon(points, fill=color)

        return w + 12

    def draw_time(self, draw, x, y, current_time):
        """Draw large segmented time display."""
        time_str = current_time.strftime("%H:%M")

        # Japanese label
        draw.text((x, y - 22), config.LABELS["time"],
                  font=self.fonts["jp"], fill=self._get_color("secondary"))

        # Draw segmented digits (larger size)
        offset_x = x
        for char in time_str:
            width = self.draw_segmented_digit(draw, offset_x, y, char, size=90, thickness=12)
            offset_x += width

        # Seconds
        seconds = current_time.strftime(":%S")
        draw.text((offset_x + 8, y + 55), seconds,
                  font=self.fonts["medium"], fill=self._get_color("primary"))

    def draw_date(self, draw, x, y, current_time):
        """Draw date display."""
        draw.text((x, y), config.LABELS["date"],
                  font=self.fonts["jp"], fill=self._get_color("secondary"))

        date_str = current_time.strftime("%Y.%m.%d")
        day_str = current_time.strftime("%A").upper()

        draw.text((x, y + 18), date_str,
                  font=self.fonts["medium"], fill=self._get_color("primary"))
        draw.text((x + 160, y + 18), day_str,
                  font=self.fonts["medium"], fill=self._get_color("accent"))

    def draw_daylight_arc(self, draw, x, y, width, height, current_time):
        """Draw 24-hour sun arc with S-curves for night."""
        try:
            s = sun(self.location.observer, date=current_time.date(),
                   tzinfo=self.location.timezone)
            sunrise = s["sunrise"]
            sunset = s["sunset"]
        except Exception as e:
            draw.text((x, y), f"Sun calc error: {e}",
                     font=self.fonts["small"], fill=self._get_color("accent"))
            return

        draw.text((x, y), config.LABELS["daylight"],
                  font=self.fonts["jp"], fill=self._get_color("secondary"))

        arc_y = y + 22
        arc_height = height - 45

        # Time calculations
        midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        sunrise_naive = sunrise.replace(tzinfo=None)
        sunset_naive = sunset.replace(tzinfo=None)
        midnight_naive = midnight.replace(tzinfo=None) if midnight.tzinfo else midnight
        current_naive = current_time.replace(tzinfo=None) if current_time.tzinfo else current_time

        sunrise_frac = (sunrise_naive - midnight_naive).total_seconds() / 86400
        sunset_frac = (sunset_naive - midnight_naive).total_seconds() / 86400
        horizon_y = arc_y + arc_height // 2

        def get_sun_height(time_frac):
            if sunrise_frac <= time_frac <= sunset_frac:
                day_progress = (time_frac - sunrise_frac) / (sunset_frac - sunrise_frac)
                return arc_height // 2 * math.sin(day_progress * math.pi)
            elif time_frac < sunrise_frac:
                night_progress = time_frac / sunrise_frac
                return -arc_height // 4 * math.cos(night_progress * math.pi / 2)
            else:
                night_progress = (time_frac - sunset_frac) / (1 - sunset_frac)
                return -arc_height // 4 * math.sin(night_progress * math.pi / 2)

        # Draw arc path
        arc_color = self._get_color("secondary")
        prev_point = None
        for i in range(width + 1):
            time_frac = i / width
            sun_h = get_sun_height(time_frac)
            point = (x + i, horizon_y - sun_h)
            if prev_point:
                draw.line([prev_point, point], fill=arc_color, width=2)
            prev_point = point

        # Horizon line
        draw.line([(x, horizon_y), (x + width, horizon_y)],
                 fill=self._get_color("primary"), width=1)

        # Sunrise line and label
        sunrise_x = x + int(sunrise_frac * width)
        draw.line([(sunrise_x, arc_y), (sunrise_x, horizon_y + arc_height // 4)],
                 fill=self._get_color("warning"), width=1)
        sunrise_str = sunrise.strftime("%H:%M")
        draw.text((sunrise_x - 42, horizon_y + arc_height // 4 + 2), sunrise_str,
                  font=self.fonts["small"], fill=self._get_color("warning"))

        # Sunset line and label
        sunset_x = x + int(sunset_frac * width)
        draw.line([(sunset_x, arc_y), (sunset_x, horizon_y + arc_height // 4)],
                 fill=self._get_color("accent"), width=1)
        sunset_str = sunset.strftime("%H:%M")
        draw.text((sunset_x + 5, horizon_y + arc_height // 4 + 2), sunset_str,
                  font=self.fonts["small"], fill=self._get_color("accent"))

        # Current sun position
        now_frac = (current_naive - midnight_naive).total_seconds() / 86400
        sun_h = get_sun_height(now_frac)
        sun_x = x + int(now_frac * width)
        sun_y = int(horizon_y - sun_h)

        is_day = sunrise_frac <= now_frac <= sunset_frac
        sun_color = self._get_color("warning") if is_day else self._get_color("accent")
        sun_radius = 7
        draw.ellipse([sun_x - sun_radius, sun_y - sun_radius,
                     sun_x + sun_radius, sun_y + sun_radius],
                    fill=sun_color)

    def draw_events(self, draw, x, y, width, max_events=5):
        """Draw upcoming calendar events with colored symbols."""
        draw.text((x, y), "予定 / UPCOMING",
                  font=self.fonts["small"], fill=self._get_color("accent"))

        event_y = y + 22
        line_height = 20

        if not self.events:
            draw.text((x, event_y), "No upcoming events",
                     font=self.fonts["small"], fill=self._get_color("secondary"))
            return

        for i, event in enumerate(self.events[:max_events]):
            symbol = event.get("symbol", "●")
            time_str = event.get("time", "")
            title = event.get("title", "Untitled")
            color_name = event.get("color", "primary")

            # Get color for this calendar
            event_color = self.colors.get(color_name, self._get_color("primary"))

            # Truncate title if needed
            max_title_len = 30
            if len(title) > max_title_len:
                title = title[:max_title_len - 2] + ".."

            # Symbol in calendar color
            draw.text((x, event_y), symbol, font=self.fonts["small"], fill=event_color)

            # Time
            time_x = x + 18
            draw.text((time_x, event_y), time_str,
                     font=self.fonts["small"], fill=self._get_color("secondary"))

            # Title
            title_x = time_x + 65
            draw.text((title_x, event_y), title,
                     font=self.fonts["small"], fill=self._get_color("primary"))

            event_y += line_height

    def render(self, page_index=0, total_pages=1):
        """Render the dashboard page."""
        image, draw = super().render(page_index, total_pages)
        now = datetime.now()

        # Fetch events if needed
        if not self._last_fetch:
            self.refresh_events()

        margin = 20
        content_top = 45

        # Time display (large, top-left)
        self.draw_time(draw, margin, content_top, now)

        # Date display (below time)
        self.draw_date(draw, margin, content_top + 115, now)

        # Border around time/date section
        self.draw_border_frame(draw, margin - 5, content_top - 25, 340, 160)

        # Daylight arc (full width, middle)
        arc_y = content_top + 165
        self.draw_daylight_arc(draw, margin, arc_y, self.width - (margin * 2), 95, now)
        self.draw_border_frame(draw, margin - 5, arc_y - 5, self.width - (margin * 2) + 10, 100)

        # Events section (right side of screen, next to time)
        events_x = 380
        events_y = content_top - 25
        self.draw_events(draw, events_x, events_y, self.width - events_x - margin, max_events=6)
        self.draw_border_frame(draw, events_x - 10, events_y - 5, self.width - events_x - margin + 15, 155)

        return image
