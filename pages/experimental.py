"""
Experimental Page - Placeholder for future projects
Ideas: system stats, camera feeds, data visualizations, etc.
"""

from datetime import datetime
from pages.base import Page
import config


class ExperimentalPage(Page):
    """Experimental page for future projects."""

    name = "experimental"
    title = "EXPERIMENTAL"
    title_jp = "実験"

    def __init__(self, width, height, fonts):
        super().__init__(width, height, fonts)

    def draw_placeholder_box(self, draw, x, y, width, height, label):
        """Draw a placeholder box for future content."""
        # Dashed border effect (just corners for now)
        color = self._get_color("secondary")

        # Corner brackets
        bracket_len = 15
        # Top-left
        draw.line([(x, y), (x + bracket_len, y)], fill=color, width=1)
        draw.line([(x, y), (x, y + bracket_len)], fill=color, width=1)
        # Top-right
        draw.line([(x + width - bracket_len, y), (x + width, y)], fill=color, width=1)
        draw.line([(x + width, y), (x + width, y + bracket_len)], fill=color, width=1)
        # Bottom-left
        draw.line([(x, y + height - bracket_len), (x, y + height)], fill=color, width=1)
        draw.line([(x, y + height), (x + bracket_len, y + height)], fill=color, width=1)
        # Bottom-right
        draw.line([(x + width - bracket_len, y + height), (x + width, y + height)], fill=color, width=1)
        draw.line([(x + width, y + height - bracket_len), (x + width, y + height)], fill=color, width=1)

        # Label in center
        draw.text((x + width // 2 - 40, y + height // 2 - 8), label,
                  font=self.fonts["small"], fill=color)

    def render(self, page_index=0, total_pages=1):
        """Render the experimental page."""
        image, draw = super().render(page_index, total_pages)

        margin = 20
        content_top = 50

        # Title
        draw.text((margin, content_top), "EXPERIMENTAL LAB",
                  font=self.fonts["medium"], fill=self._get_color("accent"))
        draw.text((margin, content_top + 28), "実験室 - Future projects go here",
                  font=self.fonts["small"], fill=self._get_color("secondary"))

        # Placeholder boxes for future features
        box_width = (self.width - margin * 3) // 2
        box_height = 120

        # Row 1
        self.draw_placeholder_box(draw, margin, content_top + 70,
                                  box_width, box_height, "SYSTEM STATS")
        self.draw_placeholder_box(draw, margin * 2 + box_width, content_top + 70,
                                  box_width, box_height, "WEATHER")

        # Row 2
        self.draw_placeholder_box(draw, margin, content_top + 70 + box_height + 15,
                                  box_width, box_height, "CAMERA FEED")
        self.draw_placeholder_box(draw, margin * 2 + box_width, content_top + 70 + box_height + 15,
                                  box_width, box_height, "DATA VIZ")

        # Ideas list at bottom
        ideas_y = self.height - 60
        draw.text((margin, ideas_y), "Ideas: Pi stats, security cam, weather, quotes, pomodoro...",
                  font=self.fonts["small"], fill=self._get_color("secondary"))

        return image
