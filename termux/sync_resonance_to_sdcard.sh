#!/data/data/com.termux/files/usr/bin/bash
# Sync resonance.sqlite3 from Termux to /sdcard/ariannamethod/
# This makes it accessible to Molly Widget and Mac daemon

TERMUX_DB="$HOME/ariannamethod/resonance.sqlite3"
SDCARD_DIR="/sdcard/ariannamethod"
SDCARD_DB="$SDCARD_DIR/resonance.sqlite3"

# Create directory if needed
mkdir -p "$SDCARD_DIR"

# Copy if source exists
if [ -f "$TERMUX_DB" ]; then
    cp "$TERMUX_DB" "$SDCARD_DB"
    echo "✓ resonance.sqlite3 synced to $SDCARD_DB"
else
    echo "✗ Source DB not found: $TERMUX_DB"
    exit 1
fi

