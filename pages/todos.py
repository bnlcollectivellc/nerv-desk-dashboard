"""
Todos Page - Notion integration
Today's tasks, Non-Negotiables, and Goals
"""

from datetime import datetime
from pages.base import Page
import config


class TodosPage(Page):
    """Todo list page with Notion integration, Non-Negotiables, and Goals."""

    name = "todos"
    title = "TASK LIST"
    title_jp = "タスク一覧"

    # Static content
    NON_NEGOTIABLES = [
        "Gym",
        "Meditate",
        "Work",
        "Shallows",
        "Sunset",
        "Read",
        "Dir.Img",
    ]

    GOALS = [
        "Kind, intentional, sympathetic life",
        "$250k/yr",
        "Deep Relationships",
        "Consistent Physical Health",
        "Progressive Mental Health",
        "Expansive Spiritual Health",
        "Travel",
    ]

    THEME = "THEME: Intentional, Slow, Present"

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

    def draw_bullet(self, draw, x, y, color=None):
        """Draw a bullet point."""
        if color is None:
            color = self._get_color("primary")
        draw.ellipse([x, y + 4, x + 6, y + 10], fill=color)

    def draw_todo_item(self, draw, x, y, todo, max_width=280, show_date_width=50):
        """Draw a single todo item with checkbox, title, and optional due indicator."""
        title = todo.get("title", "Untitled")
        done = todo.get("done", False)
        is_overdue = todo.get("is_overdue", False)
        due_date = todo.get("due_date")

        # Checkbox
        self.draw_checkbox(draw, x, y + 1, done, is_overdue, size=14)

        # Calculate available width for title (leave space for date if overdue)
        title_start_x = x + 22
        if is_overdue and due_date:
            available_width = max_width - 22 - show_date_width - 10
        else:
            available_width = max_width - 22 - 10

        # Truncate title based on available pixel width
        char_width = 9  # Approximate char width in small font
        max_chars = max(10, available_width // char_width)
        if len(title) > max_chars:
            title = title[:max_chars - 2] + ".."

        # Color based on state
        if done:
            text_color = self._get_color("secondary")
        elif is_overdue:
            text_color = self._get_color("accent")
        else:
            text_color = self._get_color("primary")

        draw.text((title_start_x, y), title, font=self.fonts["small"], fill=text_color)

        # Due date indicator on right side if overdue
        if is_overdue and due_date:
            due_str = due_date.strftime("%m/%d")
            draw.text((x + max_width - show_date_width, y), due_str,
                     font=self.fonts["small"], fill=self._get_color("accent"))

    def draw_non_negotiables(self, draw, x, y, width, height):
        """Draw the Non-Negotiables box."""
        # Header
        draw.text((x, y), "必須 / NN",
                  font=self.fonts["small"], fill=self._get_color("accent"))

        # Items
        item_y = y + 22
        line_height = 18

        for item in self.NON_NEGOTIABLES:
            self.draw_bullet(draw, x, item_y, self._get_color("warning"))
            draw.text((x + 12, item_y), item,
                     font=self.fonts["small"], fill=self._get_color("primary"))
            item_y += line_height

    def draw_goals(self, draw, x, y, width, height):
        """Draw the Goals box."""
        # Header
        draw.text((x, y), "目標 / GOALS",
                  font=self.fonts["small"], fill=self._get_color("accent"))

        # Items
        item_y = y + 22
        line_height = 18

        for i, goal in enumerate(self.GOALS, 1):
            # Number prefix
            draw.text((x, item_y), f"{i}.",
                     font=self.fonts["small"], fill=self._get_color("warning"))
            draw.text((x + 18, item_y), goal,
                     font=self.fonts["small"], fill=self._get_color("primary"))
            item_y += line_height

        # Theme at bottom
        item_y += 8
        draw.text((x, item_y), f"*{self.THEME}",
                 font=self.fonts["small"], fill=self._get_color("success"))

    def render(self, page_index=0, total_pages=1):
        """Render the todos page."""
        image, draw = super().render(page_index, total_pages)

        margin = 20
        content_top = 45

        # Fetch todos if needed (on first render or refresh)
        if not self._last_fetch:
            self.refresh_todos()

        # Layout: Top ~60% = Todos, Bottom ~40% = Non-Negotiables + Goals side by side
        # Increased top section to fit more tasks
        top_height = int((self.height - content_top - 20) * 0.58)
        bottom_height = self.height - content_top - top_height - 30
        bottom_half_y = content_top + top_height + 15

        # === TOP HALF: TODOS BOX ===
        # Header: "TODAY'S TASKS" on left (small font, matches dashboard date style)
        draw.text((margin, content_top), "TODAY'S TASKS",
                  font=self.fonts["small"], fill=self._get_color("accent"))

        # Count overdue items - right aligned
        overdue_count = sum(1 for t in self.todos if t.get("is_overdue"))
        if overdue_count > 0:
            overdue_text = f"OVERDUE: {overdue_count}"
            overdue_bbox = draw.textbbox((0, 0), overdue_text, font=self.fonts["small"])
            overdue_width = overdue_bbox[2] - overdue_bbox[0]
            draw.text((self.width - margin - overdue_width - 5, content_top),
                     overdue_text, font=self.fonts["small"], fill=self._get_color("accent"))

        # Todo list - start closer to header, tighter line height
        item_y = content_top + 22
        line_height = 18
        max_y = content_top + top_height - 10  # Leave padding at bottom
        max_items = (max_y - item_y) // line_height

        todo_box_width = self.width - margin * 2 - 10

        if not self.todos:
            draw.text((margin + 22, item_y), "No tasks due today",
                     font=self.fonts["small"], fill=self._get_color("secondary"))
        else:
            for i, todo in enumerate(self.todos[:max_items]):
                if item_y + line_height > max_y:
                    break
                self.draw_todo_item(draw, margin, item_y, todo, max_width=todo_box_width)
                item_y += line_height

            if len(self.todos) > max_items:
                remaining = len(self.todos) - max_items
                if item_y + line_height <= max_y:
                    draw.text((margin, item_y),
                             f"+ {remaining} more...",
                             font=self.fonts["small"], fill=self._get_color("secondary"))

        # Todos box border
        self.draw_border_frame(draw, margin - 5, content_top - 5,
                              self.width - margin * 2 + 10, top_height)

        # === BOTTOM HALF: NON-NEGOTIABLES + GOALS ===
        # Calculate Non-Negotiables width based on longest item
        max_nn_width = 0
        for item in self.NON_NEGOTIABLES:
            bbox = draw.textbbox((0, 0), item, font=self.fonts["small"])
            max_nn_width = max(max_nn_width, bbox[2] - bbox[0])
        nn_box_width = max_nn_width + 35  # Add padding for bullet and margins

        goals_box_x = margin + nn_box_width + 15
        goals_box_width = self.width - goals_box_x - margin + 5

        # Non-Negotiables box (left)
        self.draw_non_negotiables(draw, margin, bottom_half_y, nn_box_width, bottom_height)
        self.draw_border_frame(draw, margin - 5, bottom_half_y - 5, nn_box_width, bottom_height)

        # Goals box (right)
        self.draw_goals(draw, goals_box_x, bottom_half_y, goals_box_width, bottom_height)
        self.draw_border_frame(draw, goals_box_x - 5, bottom_half_y - 5, goals_box_width, bottom_height)

        return image
