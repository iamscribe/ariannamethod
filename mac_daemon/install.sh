#!/bin/bash
#
# Scribe Mac Daemon - Installation Script
# Installs CLI and daemon for system-wide access
#

set -e

echo "🔧 Installing Scribe Mac Daemon..."
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Install location
INSTALL_DIR="/usr/local/bin"
DAEMON_DIR="$HOME/.scribe_mac_daemon"

# Create daemon directory
echo "📁 Creating daemon directory..."
mkdir -p "$DAEMON_DIR"

# Copy daemon files
echo "📋 Copying daemon files..."
cp "$SCRIPT_DIR/scribe_mac_daemon.py" "$DAEMON_DIR/"
chmod +x "$DAEMON_DIR/scribe_mac_daemon.py"

# Install CLI
echo "🎮 Installing CLI..."
sudo cp "$SCRIPT_DIR/scribe" "$INSTALL_DIR/scribe"
sudo chmod +x "$INSTALL_DIR/scribe"

# Verify installation
if command -v scribe &> /dev/null; then
    echo ""
    echo "✅ Installation complete!"
    echo ""
    echo "📊 Test installation:"
    echo "   scribe status"
    echo ""
    echo "🚀 Start daemon:"
    echo "   python3 $DAEMON_DIR/scribe_mac_daemon.py start &"
    echo ""
    echo "💡 Or run in foreground:"
    echo "   python3 $DAEMON_DIR/scribe_mac_daemon.py start"
    echo ""
else
    echo "❌ Installation failed!"
    exit 1
fi

