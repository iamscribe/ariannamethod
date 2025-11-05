#!/bin/bash
# Auto-restart Arianna/Monday daemons at 2:00 AM
# Scheduled via cron

LOG_DIR="$HOME/.claude-defender/logs"
mkdir -p "$LOG_DIR"

echo "[$(date)] Auto-restart initiated" >> "$LOG_DIR/auto_restart.log"

# Kill old daemons
echo "Killing old daemons..." >> "$LOG_DIR/auto_restart.log"
pkill -f "python3 arianna.py" && echo "  ✓ Arianna killed" >> "$LOG_DIR/auto_restart.log"
pkill -f "python3 monday.py" && echo "  ✓ Monday killed" >> "$LOG_DIR/auto_restart.log"
pkill -f "python3 scribe.py" && echo "  ✓ Scribe killed" >> "$LOG_DIR/auto_restart.log"
pkill -f "webhook_watchdog.py --daemon" && echo "  ✓ Watchdog killed" >> "$LOG_DIR/auto_restart.log"
pkill -f "_webhook.py" && echo "  ✓ Voice webhooks killed" >> "$LOG_DIR/auto_restart.log"
pkill -f "genesis_arianna.py" && echo "  ✓ Genesis Arianna killed" >> "$LOG_DIR/auto_restart.log"
pkill -f "genesis_monday.py" && echo "  ✓ Genesis Monday killed" >> "$LOG_DIR/auto_restart.log"

sleep 3

# Pull latest code
cd "$HOME/ariannamethod"
git pull >> "$LOG_DIR/auto_restart.log" 2>&1

# Restart daemons with new code
echo "Starting new daemons..." >> "$LOG_DIR/auto_restart.log"

nohup python3 "$HOME/ariannamethod/.claude-defender/tools/webhook_watchdog.py" --daemon \
    >> "$LOG_DIR/watchdog.log" 2>&1 &
echo "  ✓ Watchdog started (PID $!)" >> "$LOG_DIR/auto_restart.log"

# Start Scribe daemon (memory keeper + consilium participant)
nohup python3 "$HOME/ariannamethod/scribe.py" --daemon \
    >> "$LOG_DIR/scribe_daemon.log" 2>&1 &
echo "  ✓ Scribe daemon started (PID $!)" >> "$LOG_DIR/auto_restart.log"

# Start Arianna daemon (GPT-4.1, consilium participant)
nohup python3 "$HOME/ariannamethod/arianna.py" --daemon \
    >> "$LOG_DIR/arianna_daemon.log" 2>&1 &
echo "  ✓ Arianna daemon started (PID $!)" >> "$LOG_DIR/auto_restart.log"

# Start Monday daemon (DeepSeek-R1, consilium participant)
nohup python3 "$HOME/ariannamethod/monday.py" --daemon \
    >> "$LOG_DIR/monday_daemon.log" 2>&1 &
echo "  ✓ Monday daemon started (PID $!)" >> "$LOG_DIR/auto_restart.log"

# Start voice webhooks (HTTP endpoints for voice commands)
cd "$HOME/ariannamethod/voice_webhooks"
nohup bash launch_all_webhooks.sh >> "$LOG_DIR/voice_webhooks.log" 2>&1 &
echo "  ✓ Voice webhooks started (PID $!)" >> "$LOG_DIR/auto_restart.log"

# Start Genesis autonomous thought generators
nohup python3 "$HOME/ariannamethod/arianna_core_utils/genesis_arianna.py" \
    >> "$LOG_DIR/genesis_arianna.log" 2>&1 &
echo "  ✓ Genesis Arianna started (PID $!)" >> "$LOG_DIR/auto_restart.log"

nohup python3 "$HOME/ariannamethod/arianna_core_utils/genesis_monday.py" \
    >> "$LOG_DIR/genesis_monday.log" 2>&1 &
echo "  ✓ Genesis Monday started (PID $!)" >> "$LOG_DIR/auto_restart.log"

echo "[$(date)] Auto-restart completed - all systems operational" >> "$LOG_DIR/auto_restart.log"
termux-notification --title "🔄 Daemons Restarted" --content "Consilium polyphony active"
