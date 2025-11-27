#!/usr/bin/env python3
"""
NERV Dashboard for Inky Impression 5.7"
神経 - Evangelion-style desk display

Multi-page dashboard with button navigation:
- A = Previous page
- B = Next page
- C = Special action (page-specific)
- D = Force refresh
"""

import sys
import time
from datetime import datetime, timedelta
from PIL import ImageFont

import config

# Import pages
from pages import DashboardPage, TodosPage, ExperimentalPage, SatellitePage

# Try to import inky, fall back to preview mode if not available
try:
    from inky.inky_uc8159 import Inky as InkyImpression
    INKY_AVAILABLE = True
except ImportError:
    INKY_AVAILABLE = False
    print("Inky not available - running in preview mode")

# Try to import GPIO for button support
try:
    import gpiod
    from gpiod.line import Bias, Edge
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("GPIO not available - buttons disabled")


class NERVDashboard:
    """NERV-style multi-page dashboard for Inky Impression."""

    def __init__(self):
        self.width = config.DISPLAY_WIDTH
        self.height = config.DISPLAY_HEIGHT

        # Initialize display
        if INKY_AVAILABLE:
            self.display = InkyImpression(resolution=(self.width, self.height))
        else:
            self.display = None

        # Load fonts
        self.fonts = self._load_fonts()

        # Initialize pages
        self.pages = {
            "dashboard": DashboardPage(self.width, self.height, self.fonts),
            "todos": TodosPage(self.width, self.height, self.fonts),
            "satellite": SatellitePage(self.width, self.height, self.fonts),
            "experimental": ExperimentalPage(self.width, self.height, self.fonts),
        }

        # Page navigation
        self.page_order = config.PAGES
        self.current_page_index = 0
        self.current_page = self.page_order[self.current_page_index]

        # Button state
        self.button_request = None

    def _load_fonts(self):
        """Load fonts for the display."""
        fonts = {}
        try:
            fonts["large"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 72)
            fonts["medium"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 24)
            fonts["small"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
            fonts["jp"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except OSError:
            # Fall back to default font
            default = ImageFont.load_default()
            fonts["large"] = default
            fonts["medium"] = default
            fonts["small"] = default
            fonts["jp"] = default
        return fonts

    def setup_buttons(self):
        """Set up GPIO button handlers for all 4 buttons."""
        if not GPIO_AVAILABLE:
            return None

        # Try Pi 5 first, then fall back to older Pi
        try:
            chip = gpiod.Chip("/dev/gpiochip4")
        except FileNotFoundError:
            try:
                chip = gpiod.Chip("/dev/gpiochip0")
            except FileNotFoundError:
                print("No GPIO chip found - buttons disabled")
                return None

        # Configure all buttons
        line_config = gpiod.LineSettings(
            edge_detection=Edge.FALLING,
            bias=Bias.PULL_UP,
            debounce_period=timedelta(milliseconds=100)
        )

        button_pins = list(config.BUTTONS.values())

        try:
            self.button_request = chip.request_lines(
                consumer="nerv-dashboard",
                config={pin: line_config for pin in button_pins}
            )
            print(f"Buttons ready: A=prev, B=next, C=special, D=refresh")
            return self.button_request
        except Exception as e:
            print(f"Could not set up buttons: {e}")
            return None

    def check_buttons(self):
        """Check for button presses and return action."""
        if self.button_request is None:
            return None

        if self.button_request.wait_edge_events(timeout=0):
            events = self.button_request.read_edge_events()
            for event in events:
                pin = event.line_offset

                if pin == config.BUTTONS["A"]:
                    print("Button A - Previous page")
                    return "prev"
                elif pin == config.BUTTONS["B"]:
                    print("Button B - Next page")
                    return "next"
                elif pin == config.BUTTONS["C"]:
                    print("Button C - Special action")
                    return "special"
                elif pin == config.BUTTONS["D"]:
                    print("Button D - Refresh")
                    return "refresh"

        return None

    def navigate(self, direction):
        """Navigate between pages."""
        if direction == "next":
            self.current_page_index = (self.current_page_index + 1) % len(self.page_order)
        elif direction == "prev":
            self.current_page_index = (self.current_page_index - 1) % len(self.page_order)

        self.current_page = self.page_order[self.current_page_index]
        print(f"Switched to page: {self.current_page}")

    def handle_special_action(self):
        """Handle page-specific special action (button C)."""
        # For now, just print - can be extended per page
        print(f"Special action on page: {self.current_page}")
        # Future: Each page could have a handle_special() method

    def render(self):
        """Render the current page."""
        page = self.pages[self.current_page]
        image = page.render(
            page_index=self.current_page_index,
            total_pages=len(self.page_order)
        )
        return image

    def update_display(self):
        """Update the Inky display with current page."""
        image = self.render()

        if self.display:
            self.display.set_image(image)
            self.display.show()
            print(f"[{self.current_page}] Display updated at {datetime.now().strftime('%H:%M:%S')}")
        else:
            # Save preview image
            image.save("preview.png")
            print(f"[{self.current_page}] Preview saved at {datetime.now().strftime('%H:%M:%S')}")

    def run(self):
        """Main loop - update display and handle buttons."""
        print("NERV Dashboard starting...")
        print(f"Pages: {', '.join(self.page_order)}")
        print(f"Update interval: {config.UPDATE_INTERVAL} seconds")
        print("-" * 40)

        # Set up buttons
        self.setup_buttons()

        # Initial update
        self.update_display()

        try:
            while True:
                # Check for button presses every 0.5 seconds
                for _ in range(config.UPDATE_INTERVAL * 2):
                    action = self.check_buttons()

                    if action == "refresh":
                        self.update_display()
                        break
                    elif action == "next":
                        self.navigate("next")
                        self.update_display()
                        break
                    elif action == "prev":
                        self.navigate("prev")
                        self.update_display()
                        break
                    elif action == "special":
                        self.handle_special_action()
                        # Don't refresh display for special action (yet)

                    time.sleep(0.5)
                else:
                    # No button press - do scheduled update
                    self.update_display()

        except KeyboardInterrupt:
            print("\nDashboard stopped.")
            sys.exit(0)


if __name__ == "__main__":
    dashboard = NERVDashboard()

    # Check for single-run mode
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        dashboard.update_display()
    elif len(sys.argv) > 1 and sys.argv[1] == "--page":
        # Preview a specific page: python main.py --page todos
        if len(sys.argv) > 2:
            page_name = sys.argv[2]
            if page_name in dashboard.pages:
                dashboard.current_page = page_name
                dashboard.current_page_index = dashboard.page_order.index(page_name)
        dashboard.update_display()
    else:
        dashboard.run()
