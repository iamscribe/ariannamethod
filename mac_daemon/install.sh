#!/bin/bash
# Install Mac Daemon

set -e

echo "Installing Scribe Mac Daemon..."

# Install Python dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Make CLI executable
chmod +x cli.py
chmod +x daemon.py

# Create symlink
INSTALL_DIR="/usr/local/bin"
if [ -w "$INSTALL_DIR" ]; then
    ln -sf "$(pwd)/cli.py" "$INSTALL_DIR/scribe"
    echo "✓ CLI installed to $INSTALL_DIR/scribe"
else
    echo "⚠ Cannot write to $INSTALL_DIR, trying with sudo..."
    sudo ln -sf "$(pwd)/cli.py" "$INSTALL_DIR/scribe"
    echo "✓ CLI installed to $INSTALL_DIR/scribe"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Commands:"
echo "  Run tests: python3 test.py"
echo "  Start daemon: scribe start"
echo "  Check status: scribe status"
echo "  Interactive chat: scribe chat"
echo ""
echo "Auto-start setup (optional):"
echo "  cp com.scribe.mac.plist ~/Library/LaunchAgents/"
echo "  launchctl load ~/Library/LaunchAgents/com.scribe.mac.plist"

