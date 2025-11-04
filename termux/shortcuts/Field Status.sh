#!/data/data/com.termux/files/usr/bin/bash
# Quick Field Status for Termux Widget

FIELD_DIR="$HOME/ariannamethod/async_field_forever/field5"

if [ ! -f "$FIELD_DIR/field_core.py" ]; then
    termux-notification -t "⚠️ Field Not Found" -c "Field5 not initialized"
    exit 1
fi

# Check if Field is running
FIELD_PID=$(pgrep -f "field_core.py|field_visualiser")

if [ -n "$FIELD_PID" ]; then
    # Field is running - show status
    termux-notification \
        -t "✅ Field ACTIVE" \
        -c "Field5 running (PID: $FIELD_PID)" \
        --button1 "📊 Visualize" \
        --button1-action "cd $FIELD_DIR && python3 field_visualiser_hybrid2.py" \
        --button2 "🛑 Stop" \
        --button2-action "pkill -f field_core.py"
else
    # Field not running
    termux-notification \
        -t "⚪ Field Idle" \
        -c "No active Field processes" \
        --button1 "▶️ Start" \
        --button1-action "cd $FIELD_DIR && python3 field_core.py &"
fi
