"""
Calendar Integration
Fetches events from iCloud ICS calendars
"""

import requests
from datetime import datetime, date, timedelta
from icalendar import Calendar
import recurring_ical_events


class CalendarClient:
    """Client for fetching events from ICS calendar URLs."""

    def __init__(self, calendars):
        """
        Initialize with list of calendar configs.
        Each config: {"url": "webcal://...", "symbol": "●", "name": "Work", "color": "red"}
        """
        self.calendars = calendars
        self._cache = {}
        self._cache_time = {}
        self.cache_minutes = 15

    def _fetch_ics(self, url):
        """Fetch and parse ICS data from URL."""
        # Convert webcal:// to https://
        if url.startswith("webcal://"):
            url = url.replace("webcal://", "https://", 1)

        # Check cache
        now = datetime.now()
        if url in self._cache:
            cache_age = (now - self._cache_time[url]).total_seconds() / 60
            if cache_age < self.cache_minutes:
                return self._cache[url]

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            cal = Calendar.from_ical(response.content)
            self._cache[url] = cal
            self._cache_time[url] = now
            return cal
        except Exception as e:
            print(f"Error fetching calendar {url}: {e}")
            return None

    def _parse_event_time(self, event):
        """Extract start time from an event, handling all-day events."""
        dtstart = event.get("dtstart")
        if not dtstart:
            return None, True  # No start time

        dt = dtstart.dt
        if isinstance(dt, datetime):
            return dt, False  # Has specific time
        elif isinstance(dt, date):
            return datetime.combine(dt, datetime.min.time()), True  # All-day event
        return None, True

    def get_events(self, days_ahead=2):
        """
        Get upcoming events from all calendars.

        Args:
            days_ahead: How many days to look ahead

        Returns:
            List of event dicts sorted by start time
        """
        today = date.today()
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today + timedelta(days=days_ahead), datetime.max.time())

        all_events = []

        for cal_config in self.calendars:
            url = cal_config.get("url")
            symbol = cal_config.get("symbol", "●")
            name = cal_config.get("name", "Calendar")
            color = cal_config.get("color", "primary")

            cal = self._fetch_ics(url)
            if not cal:
                continue

            try:
                # Get recurring events expanded
                events = recurring_ical_events.of(cal).between(start_date, end_date)
            except Exception as e:
                print(f"Error parsing events from {name}: {e}")
                continue

            for event in events:
                summary = str(event.get("summary", "Untitled"))
                start_time, is_all_day = self._parse_event_time(event)

                if start_time is None:
                    continue

                # Format time string (24hr, no colon for consistency)
                if is_all_day:
                    time_str = "ALLD"
                else:
                    time_str = start_time.strftime("%H%M")

                all_events.append({
                    "title": summary,
                    "start": start_time,
                    "time": time_str,
                    "is_all_day": is_all_day,
                    "symbol": symbol,
                    "calendar": name,
                    "color": color,
                })

        # Sort by: today first, then by time (all-day events first within a day)
        def sort_key(e):
            event_date = e["start"].date()
            is_today = event_date == today
            return (
                0 if is_today else 1,  # Today's events first
                event_date,
                0 if e["is_all_day"] else 1,  # All-day events first
                e["start"],
            )

        all_events.sort(key=sort_key)
        return all_events

    def get_events_for_display(self, max_events=20):
        """Get events formatted for dashboard display."""
        events = self.get_events(days_ahead=14)  # Look 2 weeks ahead
        return events[:max_events]


def get_calendar_events(max_events=20):
    """Fetch calendar events using config from secrets.py."""
    try:
        from secrets import CALENDARS
    except ImportError:
        print("No secrets.py found - Calendar integration disabled")
        return []

    if not CALENDARS:
        print("No calendars configured in secrets.py")
        return []

    print(f"Fetching from {len(CALENDARS)} calendars...")
    client = CalendarClient(CALENDARS)
    events = client.get_events_for_display(max_events)
    print(f"Got {len(events)} events")
    return events
