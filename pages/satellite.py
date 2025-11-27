"""
Satellite Page - Google Earth View imagery with tactical reticle overlay
Displays curated satellite imagery from around the world
"""

import re
import random
import requests
from datetime import datetime
from PIL import Image, ImageDraw
from io import BytesIO

from pages.base import Page
import config


class SatellitePage(Page):
    """Satellite imagery viewer with tactical reticle overlay."""

    name = "satellite"
    title = "SATELLITE VIEW"
    title_jp = "衛星画像"

    # Google Earth View JSON source
    EARTHVIEW_JSON_URL = "https://raw.githubusercontent.com/limhenry/earthview/master/earthview.json"

    def __init__(self, width, height, fonts):
        super().__init__(width, height, fonts)
        self.images_data = []
        self.current_image_index = 0
        self._last_fetch = None
        self._cached_image = None
        self._cache_index = -1

    def fetch_image_list(self):
        """Fetch list of available Earth View images."""
        try:
            response = requests.get(self.EARTHVIEW_JSON_URL, timeout=15)
            response.raise_for_status()
            self.images_data = response.json()
            # Shuffle for variety
            random.shuffle(self.images_data)
            self._last_fetch = datetime.now()
            print(f"Fetched {len(self.images_data)} Earth View images")
            return True
        except Exception as e:
            print(f"Error fetching Earth View list: {e}")
            return False

    def parse_coordinates(self, map_url):
        """Extract lat/lon from Google Maps URL."""
        try:
            # URL format: https://www.google.com/maps/@45.962714,7.724891,16z/...
            match = re.search(r'@([-\d.]+),([-\d.]+)', map_url)
            if match:
                lat = float(match.group(1))
                lon = float(match.group(2))
                return lat, lon
        except:
            pass
        return None, None

    def fetch_image(self, image_data):
        """Fetch actual image from Google's servers."""
        try:
            image_url = image_data.get("image", "")
            if not image_url:
                return None

            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            image = Image.open(BytesIO(response.content))
            return image
        except Exception as e:
            print(f"Error fetching Earth View image: {e}")
            return None

    def draw_reticle(self, draw, center_x, center_y, size):
        """Draw tactical reticle overlay in orange."""
        orange = self._get_color("accent")  # Orange/red accent color

        # Main crosshair lines (extending from center)
        line_length = size // 3
        gap = 15  # Gap at center

        # Horizontal lines
        draw.line([(center_x - line_length, center_y), (center_x - gap, center_y)],
                  fill=orange, width=1)
        draw.line([(center_x + gap, center_y), (center_x + line_length, center_y)],
                  fill=orange, width=1)

        # Vertical lines
        draw.line([(center_x, center_y - line_length), (center_x, center_y - gap)],
                  fill=orange, width=1)
        draw.line([(center_x, center_y + gap), (center_x, center_y + line_length)],
                  fill=orange, width=1)

        # Center dot
        dot_radius = 2
        draw.ellipse([center_x - dot_radius, center_y - dot_radius,
                     center_x + dot_radius, center_y + dot_radius], fill=orange)

        # Tick marks on crosshairs (mil dots style)
        tick_spacing = 20
        tick_size = 4

        for i in range(1, 6):
            offset = gap + (i * tick_spacing)
            if offset < line_length:
                # Horizontal ticks
                draw.line([(center_x - offset, center_y - tick_size),
                          (center_x - offset, center_y + tick_size)], fill=orange, width=1)
                draw.line([(center_x + offset, center_y - tick_size),
                          (center_x + offset, center_y + tick_size)], fill=orange, width=1)
                # Vertical ticks
                draw.line([(center_x - tick_size, center_y - offset),
                          (center_x + tick_size, center_y - offset)], fill=orange, width=1)
                draw.line([(center_x - tick_size, center_y + offset),
                          (center_x + tick_size, center_y + offset)], fill=orange, width=1)

        # Corner brackets
        bracket_size = 30
        bracket_offset = size // 4

        corners = [
            (center_x - bracket_offset, center_y - bracket_offset),  # Top-left
            (center_x + bracket_offset, center_y - bracket_offset),  # Top-right
            (center_x - bracket_offset, center_y + bracket_offset),  # Bottom-left
            (center_x + bracket_offset, center_y + bracket_offset),  # Bottom-right
        ]

        # Top-left corner
        draw.line([(corners[0][0], corners[0][1]),
                  (corners[0][0] + bracket_size, corners[0][1])], fill=orange, width=1)
        draw.line([(corners[0][0], corners[0][1]),
                  (corners[0][0], corners[0][1] + bracket_size)], fill=orange, width=1)

        # Top-right corner
        draw.line([(corners[1][0], corners[1][1]),
                  (corners[1][0] - bracket_size, corners[1][1])], fill=orange, width=1)
        draw.line([(corners[1][0], corners[1][1]),
                  (corners[1][0], corners[1][1] + bracket_size)], fill=orange, width=1)

        # Bottom-left corner
        draw.line([(corners[2][0], corners[2][1]),
                  (corners[2][0] + bracket_size, corners[2][1])], fill=orange, width=1)
        draw.line([(corners[2][0], corners[2][1]),
                  (corners[2][0], corners[2][1] - bracket_size)], fill=orange, width=1)

        # Bottom-right corner
        draw.line([(corners[3][0], corners[3][1]),
                  (corners[3][0] - bracket_size, corners[3][1])], fill=orange, width=1)
        draw.line([(corners[3][0], corners[3][1]),
                  (corners[3][0], corners[3][1] - bracket_size)], fill=orange, width=1)

        # Range circle
        circle_radius = size // 5
        draw.ellipse([center_x - circle_radius, center_y - circle_radius,
                     center_x + circle_radius, center_y + circle_radius],
                    outline=orange, width=1)

    def draw_data_overlay(self, draw, image_data, x, y):
        """Draw data information overlay in bottom-right, right-aligned."""
        green = self._get_color("success")  # Green for data

        if not image_data:
            draw.text((x, y), "NO DATA", font=self.fonts["small"], fill=green, anchor="ra")
            return

        # Extract coordinates from map URL
        map_url = image_data.get("map", "")
        lat, lon = self.parse_coordinates(map_url)

        # Location info
        country = image_data.get("country", "Unknown")
        region = image_data.get("region", "")

        # Format coordinates
        if lat is not None and lon is not None:
            lat_dir = "N" if lat >= 0 else "S"
            lon_dir = "E" if lon >= 0 else "W"
            coord_str = f"{abs(lat):.4f}{lat_dir} {abs(lon):.4f}{lon_dir}"
        else:
            coord_str = "COORDS: N/A"

        # Build location string
        if region:
            location_str = f"{region.upper()}, {country.upper()}"
        else:
            location_str = country.upper()

        # Truncate if too long
        if len(location_str) > 30:
            location_str = location_str[:28] + ".."

        # Draw data lines (right-aligned from x position)
        line_height = 16
        current_y = y

        # Coordinates
        draw.text((x, current_y), coord_str, font=self.fonts["small"], fill=green, anchor="ra")
        current_y += line_height

        # Location name
        draw.text((x, current_y), location_str, font=self.fonts["small"], fill=green, anchor="ra")
        current_y += line_height

        # Altitude info (typical satellite altitude)
        draw.text((x, current_y), "ALT: ~680 KM", font=self.fonts["small"], fill=green, anchor="ra")
        current_y += line_height

        # Source
        draw.text((x, current_y), "SRC: GOOGLE EARTH VIEW", font=self.fonts["small"], fill=green, anchor="ra")

    def render(self, page_index=0, total_pages=1):
        """Render the satellite page."""
        # Create base image (black background)
        image = Image.new("RGB", (self.width, self.height), self.colors["black"])
        draw = ImageDraw.Draw(image)

        # Fetch image list if needed
        if not self._last_fetch or not self.images_data:
            self.fetch_image_list()

        # Get current image data
        current_data = None
        if self.images_data:
            self.current_image_index = self.current_image_index % len(self.images_data)
            current_data = self.images_data[self.current_image_index]

            # Fetch and display satellite image
            if self._cache_index != self.current_image_index or self._cached_image is None:
                sat_image = self.fetch_image(current_data)
                if sat_image:
                    self._cached_image = sat_image
                    self._cache_index = self.current_image_index

            if self._cached_image:
                # Resize image to fill entire display
                sat_img = self._cached_image.copy()

                # Resize to fill display (crop to fit)
                img_ratio = sat_img.width / sat_img.height
                display_ratio = self.width / self.height

                if img_ratio > display_ratio:
                    # Image is wider - fit height, crop width
                    new_height = self.height
                    new_width = int(new_height * img_ratio)
                else:
                    # Image is taller - fit width, crop height
                    new_width = self.width
                    new_height = int(new_width / img_ratio)

                sat_img = sat_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Center crop
                left = (new_width - self.width) // 2
                top = (new_height - self.height) // 2
                sat_img = sat_img.crop((left, top, left + self.width, top + self.height))

                # Convert to RGB if necessary
                if sat_img.mode != "RGB":
                    sat_img = sat_img.convert("RGB")

                image.paste(sat_img, (0, 0))

                # Need to recreate draw object after paste
                draw = ImageDraw.Draw(image)

        # Draw thin border box (25px from edge)
        border_margin = 25
        orange = self._get_color("accent")
        draw.rectangle([border_margin, border_margin,
                       self.width - border_margin, self.height - border_margin],
                      outline=orange, width=1)

        # Draw reticle at center
        center_x = self.width // 2
        center_y = self.height // 2
        reticle_size = min(self.width, self.height) - 100
        self.draw_reticle(draw, center_x, center_y, reticle_size)

        # Draw data overlay (bottom-right, inside border)
        data_x = self.width - border_margin - 10
        data_y = self.height - border_margin - 75
        self.draw_data_overlay(draw, current_data, data_x, data_y)

        # Draw header elements (minimal, top-left)
        draw.text((border_margin + 10, border_margin + 5), "NERV",
                  font=self.fonts["medium"], fill=self._get_color("accent"))
        draw.text((border_margin + 80, border_margin + 9), "SATELLITE VIEW",
                  font=self.fonts["small"], fill=self._get_color("primary"))

        # Image counter (top-right)
        if self.images_data:
            counter_text = f"{self.current_image_index + 1}/{len(self.images_data)}"
            draw.text((self.width - border_margin - 10, border_margin + 9), counter_text,
                     font=self.fonts["small"], fill=self._get_color("success"), anchor="ra")

        # Cycle to next image for slideshow effect
        if self.images_data:
            self.current_image_index = (self.current_image_index + 1) % len(self.images_data)

        return image
