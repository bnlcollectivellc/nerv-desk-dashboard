#!/bin/bash
# Install script for NERV Dashboard systemd service
# Run this on the Raspberry Pi with: sudo bash install_service.sh

set -e

SERVICE_FILE="nerv-dashboard.service"
DEST="/etc/systemd/system/nerv-dashboard.service"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo bash install_service.sh"
    exit 1
fi

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: $SERVICE_FILE not found in current directory"
    exit 1
fi

# Copy service file
cp "$SERVICE_FILE" "$DEST"
echo "Copied service file to $DEST"

# Reload systemd
systemctl daemon-reload
echo "Reloaded systemd daemon"

# Enable service to start on boot
systemctl enable nerv-dashboard.service
echo "Enabled nerv-dashboard.service"

# Start the service
systemctl start nerv-dashboard.service
echo "Started nerv-dashboard.service"

# Show status
systemctl status nerv-dashboard.service --no-pager

echo ""
echo "Installation complete!"
echo "Useful commands:"
echo "  sudo systemctl status nerv-dashboard   - Check status"
echo "  sudo systemctl restart nerv-dashboard  - Restart service"
echo "  sudo journalctl -u nerv-dashboard -f   - View logs"
