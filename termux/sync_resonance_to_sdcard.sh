#!/data/data/com.termux/files/usr/bin/bash
# Sync resonance.sqlite3 from Termux to /sdcard/ariannamethod/
# This makes it accessible to Molly Widget and Mac daemon

TERMUX_DB="$HOME/ariannamethod/resonance.sqlite3"
SDCARD_DIR="$HOME/storage/shared/ariannamethod"
SDCARD_DB="$SDCARD_DIR/resonance.sqlite3"

# Check if storage is setup
if [ ! -d "$HOME/storage/shared" ]; then
    echo "✗ Termux storage not setup. Run: termux-setup-storage"
    exit 1
fi

# Create directory if needed
mkdir -p "$SDCARD_DIR"

# Copy if source exists
if [ -f "$TERMUX_DB" ]; then
    cp "$TERMUX_DB" "$SDCARD_DB"
    echo "✓ resonance.sqlite3 synced to $SDCARD_DB"
    echo "  (accessible from /sdcard/ariannamethod/resonance.sqlite3)"
else
    echo "✗ Source DB not found: $TERMUX_DB"
    exit 1
fi

