"""
Todos Page - Notion integration
Today's tasks and overdue items
"""

from datetime import datetime
from pages.base import Page
import config


class TodosPage(Page):
    """Todo list page with Notion integration."""

    name = "todos"
    title = "TASK LIST"
    title_jp = "タスク一覧"

    def __init__(self, width, height, fonts):
        super().__init__(width, height, fonts)
        self.todos = []
        self._last_fetch = None

    def refresh_todos(self):
        """Fetch fresh todos from Notion."""
        try:
            from integrations.notion import get_notion_todos
            self.todos = get_notion_todos()
            self._last_fetch = datetime.now()
            print(f"Fetched {len(self.todos)} todos from Notion")
        except Exception as e:
            print(f"Error fetching Notion todos: {e}")
            self.todos = []

    def draw_checkbox(self, draw, x, y, checked=False, overdue=False, size=14):
        """Draw a checkbox."""
        color = self._get_color("accent") if overdue else self._get_color("primary")
        draw.rectangle([x, y, x + size, y + size], outline=color, width=1)
        if checked:
            draw.line([(x + 3, y + size//2), (x + size//2, y + size - 3)], fill=color, width=2)
            draw.line([(x + size//2, y + size - 3), (x + size - 3, y + 3)], fill=color, width=2)

    def draw_todo_item(self, draw, x, y, todo, max_width=280):
        """Draw a single todo item with checkbox, title, and optional due indicator."""
        title = todo.get("title", "Untitled")
        done = todo.get("done", False)
        is_overdue = todo.get("is_overdue", False)
        due_date = todo.get("due_date")

        # Checkbox
        self.draw_checkbox(draw, x, y + 1, done, is_overdue, size=14)

        # Title - truncate if needed
        max_chars = 38
        if len(title) > max_chars:
            title = title[:max_chars - 2] + ".."

        # Color based on state
        if done:
            text_color = self._get_color("secondary")
        elif is_overdue:
            text_color = self._get_color("accent")
        else:
            text_color = self._get_color("primary")

        draw.text((x + 22, y), title, font=self.fonts["small"], fill=text_color)

        # Due date indicator on right side if overdue
        if is_overdue and due_date:
            due_str = due_date.strftime("%m/%d")
            draw.text((x + max_width - 40, y), due_str,
                     font=self.fonts["small"], fill=self._get_color("accent"))

    def render(self, page_index=0, total_pages=1):
        """Render the todos page."""
        image, draw = super().render(page_index, total_pages)

        margin = 20
        content_top = 45

        # Fetch todos if needed (on first render or refresh)
        if not self._last_fetch:
            self.refresh_todos()

        # Date header
        now = datetime.now()
        date_str = now.strftime("%A, %B %d").upper()
        draw.text((margin, content_top), date_str,
                  font=self.fonts["medium"], fill=self._get_color("primary"))

        # Section divider
        draw.text((margin, content_top + 28), "今日のタスク / TODAY'S TASKS",
                  font=self.fonts["small"], fill=self._get_color("accent"))

        # Count overdue items
        overdue_count = sum(1 for t in self.todos if t.get("is_overdue"))
        if overdue_count > 0:
            draw.text((self.width - margin - 120, content_top + 28),
                     f"OVERDUE: {overdue_count}",
                     font=self.fonts["small"], fill=self._get_color("accent"))

        # Todo list
        item_y = content_top + 55
        line_height = 24
        max_items = 14  # Fit on screen

        if not self.todos:
            # No todos message
            draw.text((margin + 22, item_y), "No tasks due today",
                     font=self.fonts["small"], fill=self._get_color("secondary"))
            draw.text((margin + 22, item_y + line_height),
                     "Check secrets.py for Notion setup",
                     font=self.fonts["small"], fill=self._get_color("secondary"))
        else:
            for i, todo in enumerate(self.todos[:max_items]):
                self.draw_todo_item(draw, margin, item_y, todo, max_width=self.width - margin * 2)
                item_y += line_height

            # Overflow indicator
            if len(self.todos) > max_items:
                remaining = len(self.todos) - max_items
                draw.text((margin, item_y),
                         f"+ {remaining} more tasks...",
                         font=self.fonts["small"], fill=self._get_color("secondary"))

        # Border around content area
        self.draw_border_frame(draw, margin - 5, content_top - 5,
                              self.width - margin * 2 + 10, self.height - content_top - 25)

        # Last updated timestamp at bottom
        if self._last_fetch:
            updated_str = f"Updated: {self._last_fetch.strftime('%H:%M')}"
            draw.text((self.width - margin - 100, self.height - 35),
                     updated_str, font=self.fonts["small"],
                     fill=self._get_color("secondary"))

        return image
