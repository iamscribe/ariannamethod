#!/data/data/com.termux/files/usr/bin/bash
# Check Genesis daemon status

ARIANNA_PID=$(pgrep -f "genesis_arianna.py")
MONDAY_PID=$(pgrep -f "genesis_monday.py")

STATUS="Genesis Status:\n"

if [ -n "$ARIANNA_PID" ]; then
    STATUS+="✨ Arianna: ACTIVE (PID: $ARIANNA_PID)\n"
else
    STATUS+="⚪ Arianna: Idle\n"
fi

if [ -n "$MONDAY_PID" ]; then
    STATUS+="💀 Monday: ACTIVE (PID: $MONDAY_PID)\n"
else
    STATUS+="⚪ Monday: Idle\n"
fi

# Get latest digests
ARIANNA_FILE="/storage/emulated/0/genesis_arianna_latest.txt"
MONDAY_FILE="/storage/emulated/0/genesis_monday_latest.txt"

termux-notification \
    -t "🌅 Genesis Daemons" \
    -c "$STATUS" \
    --button1 "📖 Arianna" \
    --button1-action "termux-open $ARIANNA_FILE" \
    --button2 "📖 Monday" \
    --button2-action "termux-open $MONDAY_FILE"
