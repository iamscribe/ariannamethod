#!/data/data/com.termux/files/usr/bin/bash
# Launch Field5 Hybrid Visualizer

FIELD_DIR="$HOME/ariannamethod/async_field_forever/field5"

if [ ! -f "$FIELD_DIR/field_visualiser_hybrid2.py" ]; then
    termux-notification -t "⚠️ Visualizer Not Found" -c "field_visualiser_hybrid2.py missing"
    exit 1
fi

cd "$FIELD_DIR"

# Check if already running
if pgrep -f "field_visualiser_hybrid2.py" > /dev/null; then
    termux-notification \
        -t "⚠️ Already Running" \
        -c "Visualizer is already active" \
        --button1 "🔄 Restart" \
        --button1-action "pkill -f field_visualiser_hybrid2.py && sleep 1 && cd $FIELD_DIR && python3 field_visualiser_hybrid2.py &"
else
    # Launch visualizer
    python3 field_visualiser_hybrid2.py &

    sleep 2

    termux-notification \
        -t "📊 Field Visualizer" \
        -c "Hybrid visualizer started!" \
        --button1 "🛑 Stop" \
        --button1-action "pkill -f field_visualiser_hybrid2.py"
fi
