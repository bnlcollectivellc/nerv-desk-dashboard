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

    def draw_time(self, draw, x, y, current_time, box_width):
        """Draw large segmented time display, centered in box."""
        time_str = current_time.strftime("%H:%M")

        # Calculate total width of time display to center it
        # Each digit is ~size//2 + 12, colon is ~size//4 + 8
        digit_width = 90 // 2 + 12  # 57
        colon_width = 90 // 4 + 8   # 30.5
        total_time_width = (4 * digit_width) + colon_width  # 4 digits + 1 colon

        # Center the time in the box
        start_x = x + (box_width - total_time_width) // 2

        # Japanese label (centered above time)
        label_bbox = draw.textbbox((0, 0), config.LABELS["time"], font=self.fonts["jp"])
        label_width = label_bbox[2] - label_bbox[0]
        draw.text((x + (box_width - label_width) // 2, y - 22), config.LABELS["time"],
                  font=self.fonts["jp"], fill=self._get_color("secondary"))

        # Draw segmented digits (larger size)
        offset_x = start_x
        for char in time_str:
            width = self.draw_segmented_digit(draw, offset_x, y, char, size=90, thickness=12)
            offset_x += width

        # Return the left edge of time for date alignment
        return start_x

    def draw_date(self, draw, x, y, current_time, box_width):
        """Draw date display using medium font (25% larger), centered in box."""
        date_str = current_time.strftime("%Y.%m.%d")
        day_str = current_time.strftime("%a").upper()  # Short day name (MON, TUE, etc.)
        full_date = f"{date_str} {day_str}"

        # Use medium font (25% larger than small)
        date_bbox = draw.textbbox((0, 0), full_date, font=self.fonts["medium"])
        date_width = date_bbox[2] - date_bbox[0]

        # Center the date in the box
        date_x = x + (box_width - date_width) // 2

        draw.text((date_x, y), date_str,
                  font=self.fonts["medium"], fill=self._get_color("primary"))

        # Day of week after date
        date_only_bbox = draw.textbbox((0, 0), date_str + " ", font=self.fonts["medium"])
        day_x = date_x + date_only_bbox[2] - date_only_bbox[0]
        draw.text((day_x, y), day_str,
                  font=self.fonts["medium"], fill=self._get_color("accent"))

    def draw_placeholder_module(self, draw, x, y, width, height):
        """Draw placeholder for future module (word of day, verse, etc.)."""
        # Header
        draw.text((x, y), "モジュール / MODULE",
                  font=self.fonts["small"], fill=self._get_color("accent"))

        # Centered N/A placeholder
        na_text = "N/A"
        na_bbox = draw.textbbox((0, 0), na_text, font=self.fonts["medium"])
        na_width = na_bbox[2] - na_bbox[0]
        na_height = na_bbox[3] - na_bbox[1]

        na_x = x + (width - na_width) // 2
        na_y = y + (height - na_height) // 2

        draw.text((na_x, na_y), na_text,
                 font=self.fonts["medium"], fill=self._get_color("secondary"))

    def draw_daylight_arc(self, draw, x, y, width, height, current_time):
        """Draw 24-hour sun arc with S-curves for night, no box."""
        try:
            s = sun(self.location.observer, date=current_time.date(),
                   tzinfo=self.location.timezone)
            sunrise = s["sunrise"]
            sunset = s["sunset"]
        except Exception as e:
            draw.text((x, y), f"Sun calc error: {e}",
                     font=self.fonts["small"], fill=self._get_color("accent"))
            return

        arc_y = y
        arc_height = height - 25

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
        draw.line([(sunrise_x, arc_y), (sunrise_x, horizon_y + 15)],
                 fill=self._get_color("warning"), width=1)
        sunrise_str = sunrise.strftime("%H:%M")
        draw.text((sunrise_x - 15, arc_y - 15), sunrise_str,
                  font=self.fonts["small"], fill=self._get_color("warning"))

        # Sunset line and label
        sunset_x = x + int(sunset_frac * width)
        draw.line([(sunset_x, arc_y), (sunset_x, horizon_y + 15)],
                 fill=self._get_color("accent"), width=1)
        sunset_str = sunset.strftime("%H:%M")
        draw.text((sunset_x - 15, arc_y - 15), sunset_str,
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

    def draw_events(self, draw, x, y, width, height):
        """Draw upcoming calendar events grouped by day with date headers."""
        draw.text((x, y), "予定 / UPCOMING",
                  font=self.fonts["small"], fill=self._get_color("accent"))

        event_y = y + 20
        line_height = 16
        header_height = 18
        padding = 8
        max_y = y + height - padding

        if not self.events:
            draw.text((x, event_y), "No upcoming events",
                     font=self.fonts["small"], fill=self._get_color("secondary"))
            return

        # Group events by date
        from collections import defaultdict
        events_by_date = defaultdict(list)
        for event in self.events:
            event_date = event.get("start")
            if event_date:
                date_key = event_date.strftime("%Y-%m-%d")
                events_by_date[date_key].append(event)

        # Sort dates
        sorted_dates = sorted(events_by_date.keys())

        # Calculate max title chars
        char_width = 9
        max_title_chars = max(10, (width - 70) // char_width)

        for date_key in sorted_dates:
            if event_y > max_y:
                break

            # Parse date for header
            date_obj = datetime.strptime(date_key, "%Y-%m-%d")
            date_header = date_obj.strftime("%A %m.%d").upper()  # "THURSDAY 11.27"

            # Draw date header
            draw.text((x, event_y), date_header,
                     font=self.fonts["small"], fill=self._get_color("warning"))
            event_y += header_height

            # Draw events for this date
            for event in events_by_date[date_key]:
                if event_y > max_y:
                    break

                symbol = event.get("symbol", "●")
                time_str = event.get("time", "")
                title = event.get("title", "Untitled")
                color_name = event.get("color", "primary")

                # Truncate title if needed
                if len(title) > max_title_chars:
                    title = title[:max_title_chars - 2] + ".."

                # Get color for this calendar
                event_color = self.colors.get(color_name, self._get_color("primary"))

                # Symbol
                draw.text((x + 5, event_y), symbol, font=self.fonts["small"], fill=event_color)

                # Time
                draw.text((x + 22, event_y), time_str,
                         font=self.fonts["small"], fill=self._get_color("secondary"))

                # Title
                draw.text((x + 70, event_y), title,
                         font=self.fonts["small"], fill=self._get_color("primary"))

                event_y += line_height

    def render(self, page_index=0, total_pages=1):
        """Render the dashboard page."""
        image, draw = super().render(page_index, total_pages)
        now = datetime.now()

        # Fetch events if needed
        if not self._last_fetch:
            self.refresh_events()

        # Uniform spacing constants
        margin = 15
        gap = 8  # Uniform gap between all boxes
        content_top = 35

        # Astral chart at bottom (no box, part of environment)
        arc_height = 65
        arc_y = self.height - arc_height - 5

        # Calculate available height for boxes
        available_height = arc_y - content_top - gap

        # Layout: Two columns with uniform gap
        col_gap = gap
        left_col_width = (self.width - margin * 2 - col_gap) // 2
        right_col_width = left_col_width
        right_col_x = margin + left_col_width + col_gap

        # Left column: split into time+date box (top) and placeholder box (bottom)
        left_time_box_height = (available_height - gap) // 2
        left_placeholder_height = available_height - left_time_box_height - gap
        placeholder_y = content_top + left_time_box_height + gap

        # === LEFT COLUMN: TIME+DATE BOX ===
        self.draw_border_frame(draw, margin, content_top, left_col_width, left_time_box_height)

        # Time display (centered in box)
        time_y = content_top + 15
        self.draw_time(draw, margin + 5, time_y, now, left_col_width - 10)

        # Date display (below time)
        date_y = content_top + left_time_box_height - 35
        self.draw_date(draw, margin + 5, date_y, now, left_col_width - 10)

        # === LEFT COLUMN: PLACEHOLDER MODULE BOX ===
        self.draw_border_frame(draw, margin, placeholder_y, left_col_width, left_placeholder_height)
        self.draw_placeholder_module(draw, margin + 10, placeholder_y + 10, left_col_width - 20, left_placeholder_height - 20)

        # === RIGHT COLUMN: EVENTS BOX (full height) ===
        self.draw_border_frame(draw, right_col_x, content_top, right_col_width, available_height)
        self.draw_events(draw, right_col_x + 10, content_top + 5, right_col_width - 20, available_height - 10)

        # Daylight arc at bottom (no box, no terrain)
        self.draw_daylight_arc(draw, margin, arc_y, self.width - (margin * 2), arc_height, now)

        return image
