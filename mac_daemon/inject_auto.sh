#!/bin/bash
#
# Scribe Auto-Inject - Automatic context injection into Cursor
# Uses AppleScript to paste into active Cursor window
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Generate injection context via daemon
echo "🌊 Generating Scribe context from daemon..."
"$SCRIPT_DIR/cli.py" inject > /tmp/scribe_inject_output.txt 2>&1

# Check if successful
if grep -q "✅ Scribe context copied to clipboard" /tmp/scribe_inject_output.txt; then
    echo "✅ Context ready in clipboard"
    
    # Switch to Cursor and paste automatically
    echo "🎯 Injecting into Cursor..."
    osascript <<EOF
tell application "Cursor" to activate
delay 0.5

tell application "System Events"
    -- Focus on Cursor window
    keystroke "l" using {command down, shift down}
    delay 0.3
    
    -- Paste from clipboard (Cmd+V)
    keystroke "v" using {command down}
    delay 0.2
    
    -- Send (Enter)
    keystroke return
end tell
EOF
    
    echo "🔥 Scribe identity injected into Cursor!"
    echo ""
    echo "Check Cursor - Claude should now be Scribe 🌊"
else
    echo "❌ Failed to generate context"
    cat /tmp/scribe_inject_output.txt
    exit 1
fi

