#!/data/data/com.termux/files/usr/bin/bash
#
# Genesis-1 Daemon - Dual Persona Digests
# Runs Genesis-Arianna (luminous) + Genesis-Monday (cynical) every 24 hours
# Creates impressionistic philosophical digests from artefacts/
#
# Part of Arianna Method autonomous daemon ecosystem.
#

ARIANNAMETHOD="$HOME/ariannamethod"
GENESIS_ARIANNA="$ARIANNAMETHOD/arianna_core_utils/genesis_arianna.py"
GENESIS_MONDAY="$ARIANNAMETHOD/arianna_core_utils/genesis_monday.py"
LOG_DIR="$ARIANNAMETHOD/logs"
INTERVAL=86400  # 24 hours

# Ensure logs dir exists
mkdir -p "$LOG_DIR"

# Load API keys
source ~/.bashrc

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

run_genesis_cycle() {
    log "🌅 Genesis-1 Cycle Starting"
    log "=========================================="

    # Run Genesis-Arianna (luminous philosophical digest)
    if [ -f "$GENESIS_ARIANNA" ]; then
        log "✨ Running Genesis-Arianna (luminous discovery engine)..."
        python3 "$GENESIS_ARIANNA" --once
        if [ $? -eq 0 ]; then
            log "   ✅ Genesis-Arianna completed"
        else
            log "   ⚠️  Genesis-Arianna failed"
        fi
    else
        log "   ❌ Genesis-Arianna not found: $GENESIS_ARIANNA"
    fi

    # Pause between personas
    sleep 5

    # Run Genesis-Monday (cynical tired oracle)
    if [ -f "$GENESIS_MONDAY" ]; then
        log "😮‍💨 Running Genesis-Monday (tired oracle with Termux memory)..."
        python3 "$GENESIS_MONDAY" --once
        if [ $? -eq 0 ]; then
            log "   ✅ Genesis-Monday completed"
        else
            log "   ⚠️  Genesis-Monday failed"
        fi
    else
        log "   ❌ Genesis-Monday not found: $GENESIS_MONDAY"
    fi

    log "=========================================="
    log "🌙 Genesis-1 Cycle Complete"
}

# Check if running in daemon mode
if [ "$1" = "--daemon" ]; then
    log "🛡️ Genesis-1 Daemon STARTED"
    log "   Interval: 24 hours"
    log "   Arianna: $GENESIS_ARIANNA"
    log "   Monday: $GENESIS_MONDAY"
    log ""

    while true; do
        run_genesis_cycle
        log "⏰ Next cycle in 24 hours..."
        sleep $INTERVAL
    done
elif [ "$1" = "--once" ]; then
    # Single run mode
    run_genesis_cycle
else
    # Default: single run
    run_genesis_cycle
fi
