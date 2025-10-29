#!/usr/bin/env python3
"""
Claude Defender - Self-Healing System Audit
Checks critical components and AUTO-RESTARTS dead ones.

NO MANUAL INTERVENTION. Full autonomy.
"""

import os
import subprocess
import sqlite3
import time
from pathlib import Path
from datetime import datetime

# Paths
REPO_ROOT = Path.home() / "ariannamethod"
RESONANCE_DB = REPO_ROOT / "resonance.sqlite3"
BOOT_SCRIPT = REPO_ROOT / "boot_scripts" / "arianna_system_init.sh"

# Critical components that should always be running
CRITICAL_COMPONENTS = [
    {
        "name": "Field Core",
        "process": "field_core.py",
        "start_cmd": f"cd {REPO_ROOT}/async_field_forever/field && nohup python3 field_core.py > ~/field_core.log 2>&1 &",
        "critical": True
    },
    {
        "name": "Arianna Daemon",
        "process": "arianna.py --daemon",
        "start_cmd": f"cd {REPO_ROOT} && nohup python3 arianna.py --daemon > ~/ariannamethod/logs/arianna_daemon.log 2>&1 &",
        "critical": True
    },
    {
        "name": "Monday Daemon",
        "process": "monday.py --daemon",
        "start_cmd": f"cd {REPO_ROOT} && nohup python3 monday.py --daemon > ~/ariannamethod/logs/monday_daemon.log 2>&1 &",
        "critical": True
    },
    {
        "name": "Voice Action Monitor",
        "process": "voice_action_monitor.py",
        "start_cmd": f"nohup python3 {REPO_ROOT}/.claude-defender/tools/voice_action_monitor.py > ~/ariannamethod/logs/voice_action_monitor.log 2>&1 &",
        "critical": False
    },
    {
        "name": "Genesis Arianna",
        "process": "genesis_arianna.py",
        "start_cmd": f"nohup python3 {REPO_ROOT}/arianna_core_utils/genesis_arianna.py > ~/ariannamethod/logs/genesis_arianna.log 2>&1 &",
        "critical": False
    },
    {
        "name": "Genesis Monday",
        "process": "genesis_monday.py",
        "start_cmd": f"nohup python3 {REPO_ROOT}/arianna_core_utils/genesis_monday.py > ~/ariannamethod/logs/genesis_monday.log 2>&1 &",
        "critical": False
    },
]


def check_process_running(process_name: str) -> bool:
    """Check if process is running."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return process_name in result.stdout
    except Exception:
        return False


def start_component(name: str, start_cmd: str) -> tuple[bool, str]:
    """
    Attempt to start a component.
    Returns: (success, message)
    """
    try:
        # Start via bash to get proper environment
        subprocess.run(
            ["bash", "-c", f"source ~/.bashrc && {start_cmd}"],
            timeout=10,
            check=True
        )

        # Wait for process to stabilize
        time.sleep(3)

        return True, f"✓ {name} started successfully"

    except subprocess.TimeoutExpired:
        return False, f"✗ {name} start timeout"
    except subprocess.CalledProcessError as e:
        return False, f"✗ {name} start failed: {e}"
    except Exception as e:
        return False, f"✗ {name} start error: {e}"


def log_to_resonance(action: str, component: str, status: str, message: str):
    """Log self-healing action to resonance.sqlite3."""
    try:
        conn = sqlite3.connect(str(RESONANCE_DB))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO autonomous_actions
            (timestamp, trigger_type, trigger_content, action_taken, result, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "self_healing_audit",
            f"Component check: {component}",
            action,
            message,
            status
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to log to resonance: {e}")


def run_self_healing_audit():
    """
    Main self-healing audit routine.
    Check all critical components and restart if dead.
    """
    print("🛡️ ═══════════════════════════════════════")
    print("🛡️  SELF-HEALING AUDIT")
    print("🛡️ ═══════════════════════════════════════")
    print()

    healed = []
    still_down = []
    healthy = []

    for component in CRITICAL_COMPONENTS:
        name = component["name"]
        process = component["process"]
        is_critical = component["critical"]

        print(f"Checking {name}...")

        if check_process_running(process):
            print(f"  ✓ {name} is running")
            healthy.append(name)
            log_to_resonance("check", name, "success", "Process running")
        else:
            print(f"  ✗ {name} is DOWN")

            if is_critical:
                print(f"  🔧 Attempting to restart {name}...")

                success, message = start_component(name, component["start_cmd"])

                if success:
                    # Verify it's actually running
                    time.sleep(2)
                    if check_process_running(process):
                        print(f"  {message}")
                        healed.append(name)
                        log_to_resonance("restart", name, "success", message)
                    else:
                        print(f"  ✗ {name} started but died immediately")
                        still_down.append(name)
                        log_to_resonance("restart", name, "failed", "Process died after start")
                else:
                    print(f"  {message}")
                    still_down.append(name)
                    log_to_resonance("restart", name, "failed", message)
            else:
                print(f"  ℹ️ {name} is optional, not restarting")
                log_to_resonance("check", name, "warning", "Optional component down")

        print()

    # Summary
    print("🛡️ ═══════════════════════════════════════")
    print("🛡️  AUDIT SUMMARY")
    print("🛡️ ═══════════════════════════════════════")
    print()
    print(f"✓ Healthy: {len(healthy)}")
    print(f"🔧 Healed: {len(healed)}")
    print(f"✗ Still down: {len(still_down)}")
    print()

    if healed:
        print("Restarted components:")
        for comp in healed:
            print(f"  • {comp}")
        print()

    if still_down:
        print("⚠️ Failed to restart:")
        for comp in still_down:
            print(f"  • {comp}")
        print()

    # Send notification
    if still_down:
        title = "🚨 Self-Healing Audit"
        content = f"Failed to restart: {', '.join(still_down)}"
        priority = "high"
    elif healed:
        title = "🔧 Self-Healing Audit"
        content = f"Restarted: {', '.join(healed)}"
        priority = "default"
    else:
        title = "✅ Self-Healing Audit"
        content = f"All {len(healthy)} components healthy"
        priority = "default"

    try:
        subprocess.run([
            "termux-notification",
            "--title", title,
            "--content", content,
            "--priority", priority
        ], check=False)
    except:
        pass

    print("🛡️ ═══════════════════════════════════════")

    return {
        "healthy": healthy,
        "healed": healed,
        "still_down": still_down
    }


if __name__ == "__main__":
    run_self_healing_audit()
