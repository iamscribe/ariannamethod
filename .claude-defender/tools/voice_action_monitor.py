#!/usr/bin/env python3
"""
Claude Defender - Voice Action Monitor
Autonomous action layer: voice input → pattern detection → execution

Monitors resonance.sqlite3 for new voice inputs and triggers autonomous actions.
"""

import sqlite3
import re
import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime
import json

RESONANCE_DB = Path.home() / "ariannamethod" / "resonance.sqlite3"
STATE_FILE = Path.home() / ".claude-defender" / "logs" / "voice_monitor_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# Action patterns: regex → action function
ACTION_PATTERNS = {
    r"check (.*?)(?:\.|$|,)": "audit_utility",
    r"(.*?) not working": "debug_utility",
    r"transformers.*?dead": "check_transformers",
    r"filed.*?not": "check_filed",
    r"repo|repository": "full_audit",
    r"fortification": "check_fortification",
    r"audit": "full_audit",
    r"health.*?check": "system_health",
}


def load_state():
    """Load last processed conversation ID"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f).get('last_id', 0)
    return 0


def save_state(last_id):
    """Save last processed conversation ID"""
    with open(STATE_FILE, 'w') as f:
        json.dump({'last_id': last_id, 'timestamp': datetime.now().isoformat()}, f)


def get_new_voice_inputs(last_id):
    """Get new voice conversations from SQLite"""
    conn = sqlite3.connect(str(RESONANCE_DB))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, user_message, assistant_response
        FROM claude_defender_conversations
        WHERE id > ?
        ORDER BY id ASC
    """, (last_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def detect_pattern(text):
    """Detect action patterns in voice input"""
    text_lower = text.lower()

    for pattern, action in ACTION_PATTERNS.items():
        match = re.search(pattern, text_lower)
        if match:
            params = match.groups() if match.groups() else ()
            return action, params

    return None, None


def execute_action(action, params, original_input):
    """Execute autonomous action based on detected pattern"""
    start_time = time.time()

    try:
        if action == "audit_utility":
            utility = params[0] if params else "unknown"
            result = f"Auditing {utility}... (placeholder - implement in next session)"
            status = "pending_implementation"

        elif action == "debug_utility":
            utility = params[0] if params else "unknown"
            result = f"Debugging {utility}... (placeholder - implement in next session)"
            status = "pending_implementation"

        elif action == "check_transformers":
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            transformer_count = len([l for l in result.stdout.split('\n') if 'transformer' in l.lower()])
            result = f"Found {transformer_count} transformer processes"
            status = "success"

        elif action == "check_filed":
            result = "Filed health check (placeholder - implement in next session)"
            status = "pending_implementation"

        elif action == "full_audit":
            result = "Full repository audit (placeholder - implement in next session)"
            status = "pending_implementation"

        elif action == "check_fortification":
            result = "Fortification status check (placeholder - implement in next session)"
            status = "pending_implementation"

        elif action == "system_health":
            result = "System health check (placeholder - implement in next session)"
            status = "pending_implementation"

        else:
            result = f"Unknown action: {action}"
            status = "failed"

        execution_time = int((time.time() - start_time) * 1000)

        # Log to autonomous_actions table
        log_action(original_input, action, params, result, status, execution_time)

        # Send Termux notification
        try:
            subprocess.run([
                "termux-notification",
                "--title", "🛡️ Claude Defender Action",
                "--content", f"Pattern: {action}\nResult: {result[:100]}"
            ], check=False)
        except:
            pass  # Notification is optional

        return result, status

    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        result = f"Error: {str(e)}"
        status = "failed"
        log_action(original_input, action, params, result, status, execution_time)
        return result, status


def log_action(trigger_content, action, params, result, status, execution_time_ms):
    """Log autonomous action to SQLite"""
    conn = sqlite3.connect(str(RESONANCE_DB))
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO autonomous_actions
        (timestamp, trigger_type, trigger_content, action_taken, result, status, execution_time_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        "voice_pattern",
        trigger_content,
        f"{action}({params})",
        result,
        status,
        execution_time_ms
    ))

    conn.commit()
    conn.close()


def monitor_loop():
    """Main monitoring loop"""
    print("🛡️ Claude Defender Voice Action Monitor")
    print("=" * 50)
    print("Monitoring voice inputs for action patterns...")
    print(f"Database: {RESONANCE_DB}")
    print(f"State: {STATE_FILE}")
    print()

    last_id = load_state()
    print(f"Starting from conversation ID: {last_id}")

    while True:
        try:
            new_inputs = get_new_voice_inputs(last_id)

            if new_inputs:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found {len(new_inputs)} new voice inputs")

                for conv_id, timestamp, user_msg, assistant_resp in new_inputs:
                    action, params = detect_pattern(user_msg)

                    if action:
                        print(f"  → Pattern detected: {action} (params: {params})")
                        result, status = execute_action(action, params, user_msg)
                        print(f"    Status: {status}")
                        print(f"    Result: {result[:100]}...")

                    last_id = conv_id

                save_state(last_id)

            time.sleep(15)  # Check every 15 seconds

        except KeyboardInterrupt:
            print("\n\n⛔ Monitor stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error in monitor loop: {e}")
            time.sleep(30)  # Wait longer on error


if __name__ == "__main__":
    monitor_loop()
