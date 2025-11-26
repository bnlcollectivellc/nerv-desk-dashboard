"""
Base Page class for NERV Dashboard
All pages inherit from this and implement render()
"""

from PIL import Image, ImageDraw, ImageFont
import config


class Page:
    """Base class for all dashboard pages."""

    # Page metadata (override in subclasses)
    name = "base"
    title = "BASE PAGE"
    title_jp = "ベース"

    def __init__(self, width, height, fonts):
        self.width = width
        self.height = height
        self.fonts = fonts
        self.colors = config.COLORS
        self.theme = config.THEME

    def _get_color(self, name):
        """Get RGB color tuple from theme name."""
        color_name = self.theme.get(name, name)
        return self.colors.get(color_name, self.colors["white"])

    def draw_hazard_stripes(self, draw, x, y, width, height, stripe_width=10):
        """Draw diagonal hazard stripes (yellow/black)."""
        yellow = self._get_color("warning")
        black = self.colors["black"]

        draw.rectangle([x, y, x + width, y + height], fill=yellow)

        for i in range(-height, width + height, stripe_width * 2):
            points = [
                (x + i, y + height),
                (x + i + stripe_width, y + height),
                (x + i + height + stripe_width, y),
                (x + i + height, y),
            ]
            draw.polygon(points, fill=black)

    def draw_border_frame(self, draw, x, y, width, height, thickness=2):
        """Draw NERV-style technical border with corner accents."""
        color = self._get_color("primary")

        draw.rectangle(
            [x, y, x + width, y + height],
            outline=color,
            width=thickness
        )

        corner_size = 6
        corners = [
            (x, y),
            (x + width - corner_size, y),
            (x, y + height - corner_size),
            (x + width - corner_size, y + height - corner_size),
        ]
        for cx, cy in corners:
            draw.rectangle(
                [cx, cy, cx + corner_size, cy + corner_size],
                fill=color
            )

    def draw_header(self, draw, page_index, total_pages):
        """Draw NERV-style header with hazard stripes and page indicator."""
        # Top hazard stripe
        self.draw_hazard_stripes(draw, 0, 0, self.width, 12)

        # NERV logo
        draw.text((15, 16), "NERV", font=self.fonts["medium"],
                  fill=self._get_color("accent"))

        # Page title
        draw.text((85, 20), self.title, font=self.fonts["small"],
                  fill=self._get_color("primary"))

        # Page indicator dots (right side)
        dot_radius = 4
        dot_spacing = 14
        dots_width = (total_pages * dot_spacing) - (dot_spacing - dot_radius * 2)
        start_x = self.width - dots_width - 15

        for i in range(total_pages):
            cx = start_x + (i * dot_spacing)
            cy = 24
            if i == page_index:
                # Current page - filled
                draw.ellipse([cx - dot_radius, cy - dot_radius,
                             cx + dot_radius, cy + dot_radius],
                            fill=self._get_color("primary"))
            else:
                # Other pages - outline only
                draw.ellipse([cx - dot_radius, cy - dot_radius,
                             cx + dot_radius, cy + dot_radius],
                            outline=self._get_color("primary"), width=1)

    def draw_footer(self, draw):
        """Draw bottom hazard stripe."""
        self.draw_hazard_stripes(draw, 0, self.height - 12, self.width, 12)

    def render(self, page_index=0, total_pages=1):
        """
        Render the page and return a PIL Image.
        Override this in subclasses, but call super().render() first.
        """
        image = Image.new("RGB", (self.width, self.height), self.colors["black"])
        draw = ImageDraw.Draw(image)

        self.draw_header(draw, page_index, total_pages)
        self.draw_footer(draw)

        return image, draw
