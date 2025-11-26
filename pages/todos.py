"""
Todos Page - Notion integration
Today's tasks, goals, daily non-negotiables
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
        self.goals = []
        self.non_negotiables = []

    def set_todos(self, todos, goals=None, non_negotiables=None):
        """Set todo data from Notion."""
        self.todos = todos or []
        self.goals = goals or []
        self.non_negotiables = non_negotiables or []

    def draw_checkbox(self, draw, x, y, checked=False, size=12):
        """Draw a checkbox."""
        color = self._get_color("primary")
        draw.rectangle([x, y, x + size, y + size], outline=color, width=1)
        if checked:
            # Draw checkmark
            draw.line([(x + 2, y + size//2), (x + size//2, y + size - 2)], fill=color, width=2)
            draw.line([(x + size//2, y + size - 2), (x + size - 2, y + 2)], fill=color, width=2)

    def draw_todo_section(self, draw, x, y, title, items, max_items=5):
        """Draw a section of todos with title."""
        # Section title
        draw.text((x, y), title, font=self.fonts["small"],
                  fill=self._get_color("accent"))

        item_y = y + 22

        if not items:
            draw.text((x + 20, item_y), "No items",
                     font=self.fonts["small"], fill=self._get_color("secondary"))
            return item_y + 22

        for i, item in enumerate(items[:max_items]):
            if isinstance(item, dict):
                text = item.get("title", "Untitled")
                checked = item.get("done", False)
            else:
                text = str(item)
                checked = False

            # Truncate if too long
            max_len = 35
            if len(text) > max_len:
                text = text[:max_len - 2] + ".."

            self.draw_checkbox(draw, x, item_y + 2, checked)

            text_color = self._get_color("secondary") if checked else self._get_color("primary")
            draw.text((x + 20, item_y), text, font=self.fonts["small"], fill=text_color)

            item_y += 22

        return item_y

    def render(self, page_index=0, total_pages=1):
        """Render the todos page."""
        image, draw = super().render(page_index, total_pages)

        margin = 20
        content_top = 50

        # Date header
        now = datetime.now()
        date_str = now.strftime("%A, %B %d")
        draw.text((margin, content_top), date_str,
                  font=self.fonts["medium"], fill=self._get_color("primary"))

        # Layout: Two columns
        col1_x = margin
        col2_x = self.width // 2 + 10
        section_y = content_top + 35

        # Left column: Today's Tasks
        next_y = self.draw_todo_section(draw, col1_x, section_y,
                                        "今日のタスク / TODAY", self.todos, max_items=8)

        # Right column: Goals
        self.draw_todo_section(draw, col2_x, section_y,
                              "目標 / GOALS", self.goals, max_items=4)

        # Right column: Non-negotiables (below goals)
        self.draw_todo_section(draw, col2_x, section_y + 115,
                              "必須 / NON-NEGOTIABLES", self.non_negotiables, max_items=4)

        # Border around content
        self.draw_border_frame(draw, margin - 5, content_top - 5,
                              self.width - (margin * 2) + 10, self.height - content_top - 25)

        # Placeholder message if no Notion connection
        if not self.todos and not self.goals and not self.non_negotiables:
            center_y = self.height // 2
            draw.text((self.width // 2 - 100, center_y),
                     "Connect Notion to see tasks",
                     font=self.fonts["small"], fill=self._get_color("secondary"))
            draw.text((self.width // 2 - 80, center_y + 20),
                     "See config.py for setup",
                     font=self.fonts["small"], fill=self._get_color("secondary"))

        return image
