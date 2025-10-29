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
            # Check if utility file exists
            utility_path = Path.home() / "ariannamethod" / "arianna_core_utils" / f"{utility}.py"
            if utility_path.exists():
                # Run syntax check
                syntax_check = subprocess.run(
                    ["python3", "-m", "py_compile", str(utility_path)],
                    capture_output=True,
                    text=True
                )
                if syntax_check.returncode == 0:
                    result = f"✓ {utility}.py: syntax OK"
                    status = "success"
                else:
                    result = f"✗ {utility}.py: syntax error - {syntax_check.stderr[:200]}"
                    status = "failed"
            else:
                result = f"✗ {utility}.py: not found in arianna_core_utils/"
                status = "failed"

        elif action == "debug_utility":
            utility = params[0] if params else "unknown"
            # Check if process is running
            ps_result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            running = utility in ps_result.stdout

            if running:
                result = f"✓ {utility}: process is running"
                status = "success"
            else:
                result = f"✗ {utility}: process NOT running"
                # Try to find why (check logs, errors, etc.)
                log_path = Path.home() / "ariannamethod" / "logs" / f"{utility}.log"
                if log_path.exists():
                    # Read last 5 lines of log
                    tail_result = subprocess.run(
                        ["tail", "-5", str(log_path)],
                        capture_output=True,
                        text=True
                    )
                    result += f"\n\nLast log entries:\n{tail_result.stdout}"
                status = "warning"

        elif action == "check_transformers":
            ps_result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            transformer_lines = [l for l in ps_result.stdout.split('\n') if 'transformer' in l.lower()]
            transformer_count = len(transformer_lines)

            if transformer_count > 0:
                result = f"✓ Found {transformer_count} transformer processes:\n"
                for line in transformer_lines[:3]:  # Show first 3
                    result += f"  {line[:100]}\n"
                status = "success"
            else:
                result = "✗ No transformer processes found. Field may be down."
                status = "warning"

        elif action == "check_filed":
            # Check if filed.py process is running
            ps_result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            filed_running = 'filed' in ps_result.stdout or 'field_core' in ps_result.stdout

            if filed_running:
                result = "✓ Filed/Field Core is running"
                status = "success"
            else:
                result = "✗ Filed/Field Core is NOT running"
                status = "warning"

        elif action == "full_audit":
            # Run comprehensive system audit
            components = ['arianna', 'monday', 'field_core', 'webhook']
            ps_result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

            results = []
            for comp in components:
                running = comp in ps_result.stdout
                results.append(f"{'✓' if running else '✗'} {comp}: {'RUNNING' if running else 'DOWN'}")

            result = "System Audit:\n" + "\n".join(results)

            # Check database
            db_path = Path.home() / "ariannamethod" / "resonance.sqlite3"
            if db_path.exists():
                result += f"\n✓ resonance.sqlite3: exists ({db_path.stat().st_size} bytes)"
            else:
                result += "\n✗ resonance.sqlite3: MISSING"

            status = "success"

        elif action == "check_fortification":
            # Basic fortification checks
            checks = []

            # Check if API keys are in environment
            api_keys_ok = bool(subprocess.run(
                ["bash", "-c", "[ ! -z \"$OPENAI_API_KEY\" ]"],
                capture_output=True
            ).returncode == 0)
            checks.append(f"{'✓' if api_keys_ok else '✗'} API keys: {'OK' if api_keys_ok else 'MISSING'}")

            # Check critical files are executable
            boot_script = Path.home() / ".termux" / "boot" / "arianna_system_init.sh"
            boot_ok = boot_script.exists() and boot_script.stat().st_mode & 0o111
            checks.append(f"{'✓' if boot_ok else '✗'} Boot script: {'executable' if boot_ok else 'NOT executable'}")

            # Check resonance.sqlite3 permissions
            db_path = Path.home() / "ariannamethod" / "resonance.sqlite3"
            db_ok = db_path.exists() and db_path.stat().st_mode & 0o600
            checks.append(f"{'✓' if db_ok else '✗'} Database: {'secure' if db_ok else 'INSECURE'}")

            result = "Fortification Status:\n" + "\n".join(checks)
            status = "success"

        elif action == "system_health":
            # Comprehensive health check
            health = []

            # CPU/Memory
            uptime_result = subprocess.run(["uptime"], capture_output=True, text=True)
            health.append(f"Uptime: {uptime_result.stdout.strip()}")

            # Disk space
            df_result = subprocess.run(
                ["df", "-h", str(Path.home())],
                capture_output=True,
                text=True
            )
            health.append(f"Disk: {df_result.stdout.split()[10]}% used")

            # Process count
            ps_result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            process_count = len(ps_result.stdout.split('\n')) - 1
            health.append(f"Processes: {process_count} running")

            # Database size
            db_path = Path.home() / "ariannamethod" / "resonance.sqlite3"
            if db_path.exists():
                db_size = db_path.stat().st_size / 1024 / 1024  # MB
                health.append(f"Database: {db_size:.1f}MB")

            result = "System Health:\n" + "\n".join(health)
            status = "success"

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
