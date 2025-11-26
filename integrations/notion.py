"""
Notion Integration
Fetches todos from a Notion database
"""

import requests
from datetime import datetime, date


class NotionClient:
    """Client for fetching todos from Notion."""

    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_key, database_id):
        self.api_key = api_key
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION,
        }

    def _parse_title(self, title_array):
        """Extract plain text from Notion title array."""
        if not title_array:
            return "Untitled"
        return "".join(item.get("plain_text", "") for item in title_array)

    def _parse_date(self, date_obj):
        """Parse Notion date object."""
        if not date_obj:
            return None
        start = date_obj.get("start")
        if start:
            try:
                return datetime.fromisoformat(start.replace("Z", "+00:00"))
            except ValueError:
                try:
                    return datetime.strptime(start, "%Y-%m-%d")
                except ValueError:
                    return None
        return None

    def fetch_todos(self, include_done=False):
        """
        Fetch todos from Notion database.

        Returns:
            List of todo dicts with keys: title, done, due_date, tag, is_overdue
        """
        url = f"{self.BASE_URL}/databases/{self.database_id}/query"

        # Sort by due date
        payload = {
            "sorts": [
                {"property": "Due date", "direction": "ascending"}
            ]
        }

        # Filter out done items if requested
        # Status is a "status" type with options: "Done", "Not done", "Missed"
        if not include_done:
            payload["filter"] = {
                "property": "Status",
                "status": {"does_not_equal": "Done"}
            }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Notion API error: {e}")
            return []

        todos = []
        today_date = date.today()

        for result in data.get("results", []):
            props = result.get("properties", {})

            # Parse title (Name property)
            title_prop = props.get("Name", {})
            if title_prop.get("type") == "title":
                title = self._parse_title(title_prop.get("title", []))
            else:
                title = "Untitled"

            # Parse status - "Done", "Not done", or "Missed"
            status_prop = props.get("Status", {})
            status_name = ""
            if status_prop.get("type") == "status":
                status_val = status_prop.get("status")
                if status_val:
                    status_name = status_val.get("name", "")
            done = status_name == "Done"

            # Parse due date
            due_date_prop = props.get("Due date", {})
            due_date = None
            if due_date_prop.get("type") == "date":
                due_date = self._parse_date(due_date_prop.get("date"))

            # Parse tag (multi_select)
            tag_prop = props.get("Tag", {})
            tag = ""
            if tag_prop.get("type") == "multi_select":
                tags = tag_prop.get("multi_select", [])
                tag = ", ".join(t.get("name", "") for t in tags)

            # Check if overdue
            is_overdue = False
            if due_date and not done:
                due_date_only = due_date.date() if hasattr(due_date, 'date') else due_date
                is_overdue = due_date_only < today_date

            todos.append({
                "title": title,
                "done": done,
                "due_date": due_date,
                "tag": tag,
                "is_overdue": is_overdue,
                "status": status_name,
            })

        return todos

    def get_todos_for_display(self):
        """
        Get todos formatted for display on the dashboard.
        Returns only today's todos and overdue items.
        """
        all_todos = self.fetch_todos(include_done=False)
        today = date.today()

        display_todos = []
        for todo in all_todos:
            due = todo.get("due_date")

            # Include if:
            # 1. Due today
            # 2. Overdue (past due date)
            # 3. No due date (treat as "anytime")
            include = False

            if due is None:
                include = True
            else:
                due_date_only = due.date() if hasattr(due, 'date') else due
                if due_date_only <= today:
                    include = True

            if include:
                display_todos.append(todo)

        # Sort: overdue first, then by due date
        def sort_key(t):
            if t["is_overdue"]:
                return (0, t.get("due_date") or datetime.max)
            elif t.get("due_date"):
                return (1, t["due_date"])
            else:
                return (2, datetime.max)

        display_todos.sort(key=sort_key)

        return display_todos


def get_notion_todos():
    """Fetch todos using credentials from secrets.py."""
    try:
        from secrets import NOTION_API_KEY, NOTION_DATABASE_ID
    except ImportError:
        print("No secrets.py found - Notion integration disabled")
        return []

    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        print("Notion credentials not configured in secrets.py")
        return []

    client = NotionClient(NOTION_API_KEY, NOTION_DATABASE_ID)
    return client.get_todos_for_display()
