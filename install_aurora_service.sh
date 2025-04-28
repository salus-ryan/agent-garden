#!/bin/bash
# Install Aurora as a systemd service

# Exit on error
set -e

echo "Installing Aurora as a systemd service..."

# Copy service file to systemd directory
sudo cp aurora.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable aurora.service

# Start the service
sudo systemctl start aurora.service

# Check status
sudo systemctl status aurora.service

echo "Aurora service installed and started!"
echo "To check logs: sudo journalctl -u aurora.service -f"
echo "To stop: sudo systemctl stop aurora.service"
echo "To disable autostart: sudo systemctl disable aurora.service"
