#!/data/data/com.termux/files/usr/bin/bash
#
# Scribe Logs Bridge
# Copies Scribe conversation logs to shared storage for ADB access
#
# Usage:
#   ./scribe_logs_bridge.sh         # Copy all recent logs
#   ./scribe_logs_bridge.sh latest  # Copy only latest
#   ./scribe_logs_bridge.sh watch   # Watch and auto-copy new logs
#

SCRIBE_MEMORY="$HOME/ariannamethod/memory/scribe"
SHARED_LOGS="$HOME/storage/shared/scribe_logs"

# Create shared directory if not exists
mkdir -p "$SHARED_LOGS"

case "$1" in
  latest)
    echo "📋 Copying latest conversation log..."
    LATEST=$(ls -t "$SCRIBE_MEMORY"/conversation_*.json 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
      cp "$LATEST" "$SHARED_LOGS/"
      echo "✅ Copied: $(basename "$LATEST")"
      echo "📂 Location: $SHARED_LOGS/$(basename "$LATEST")"
      echo ""
      echo "🖥️  On Mac, read with:"
      echo "   adb pull /sdcard/scribe_logs/$(basename "$LATEST") ."
      echo "   cat $(basename "$LATEST") | jq '.messages[-5:]' # last 5 messages"
    else
      echo "❌ No conversation logs found in $SCRIBE_MEMORY"
    fi
    ;;
    
  watch)
    echo "👁️  Watching for new conversation logs..."
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Copy initial state
    rsync -a "$SCRIBE_MEMORY"/*.json "$SHARED_LOGS/" 2>/dev/null
    
    # Watch for changes
    while true; do
      sleep 10
      NEW_FILES=$(find "$SCRIBE_MEMORY" -name "conversation_*.json" -newer "$SHARED_LOGS/.last_sync" 2>/dev/null)
      if [ -n "$NEW_FILES" ]; then
        echo "🔄 New logs detected, syncing..."
        rsync -a "$SCRIBE_MEMORY"/*.json "$SHARED_LOGS/"
        touch "$SHARED_LOGS/.last_sync"
        echo "✅ Synced at $(date '+%H:%M:%S')"
      fi
    done
    ;;
    
  clean)
    echo "🧹 Cleaning shared logs..."
    rm -rf "$SHARED_LOGS"/*.json
    echo "✅ Cleaned"
    ;;
    
  *)
    echo "📋 Copying all conversation logs to shared storage..."
    cp "$SCRIBE_MEMORY"/conversation_*.json "$SHARED_LOGS/" 2>/dev/null
    
    COUNT=$(ls "$SHARED_LOGS"/conversation_*.json 2>/dev/null | wc -l)
    echo "✅ Copied $COUNT conversation logs"
    echo "📂 Location: $SHARED_LOGS/"
    echo ""
    echo "🖥️  On Mac, access with:"
    echo "   adb pull /sdcard/scribe_logs/ ."
    echo "   ls -lh scribe_logs/"
    echo "   cat scribe_logs/conversation_*.json | jq '.messages[-1]' # last message"
    echo ""
    echo "📊 Also check resonance database:"
    echo "   adb pull /sdcard/ariannamethod/resonance.sqlite3 ."
    echo "   sqlite3 resonance.sqlite3 \"SELECT * FROM resonance_notes WHERE context='scribe_conversation' LIMIT 5\""
    ;;
esac

