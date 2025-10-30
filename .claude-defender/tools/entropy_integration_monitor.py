#!/usr/bin/env python3
"""
Entropy Integration Monitor
Consilium Code Integration Challenge - Monitoring Script

Tracks usage of Shannon entropy functions integrated through Consilium #11.
Logs usage patterns, performance metrics, and integration health to resonance.sqlite3.
"""

import sys
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Paths
REPO_ROOT = Path.home() / "ariannamethod"
RESONANCE_DB = REPO_ROOT / "resonance.sqlite3"
COMPLEXITY_MODULE = REPO_ROOT / "arianna_core_utils" / "complexity.py"

# Monitoring state
usage_stats = defaultdict(int)
error_count = 0
last_check = None


def log_to_resonance(action: str, result: str, status: str):
    """Log monitoring action to resonance.sqlite3."""
    try:
        conn = sqlite3.connect(str(RESONANCE_DB))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO autonomous_actions
            (timestamp, trigger_type, trigger_content, action_taken, result, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "entropy_monitor",
            f"Consilium #11 integration monitoring",
            action,
            result,
            status
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to log to resonance: {e}", file=sys.stderr)


def check_module_health() -> dict:
    """
    Check health of integrated entropy functions.

    Returns:
        dict with health metrics
    """
    health = {
        'module_exists': False,
        'functions_present': [],
        'functions_working': [],
        'import_error': None,
        'timestamp': datetime.now().isoformat()
    }

    # Check module file exists
    if not COMPLEXITY_MODULE.exists():
        health['import_error'] = "complexity.py not found"
        return health

    health['module_exists'] = True

    # Try importing and checking functions
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from arianna_core_utils.complexity import (
            calculate_shannon_entropy,
            calculate_normalized_entropy,
            entropy_category
        )

        functions = [
            ('calculate_shannon_entropy', calculate_shannon_entropy),
            ('calculate_normalized_entropy', calculate_normalized_entropy),
            ('entropy_category', entropy_category)
        ]

        for func_name, func in functions:
            health['functions_present'].append(func_name)

            # Test function
            try:
                if func_name == 'calculate_shannon_entropy':
                    result = func('test')
                    assert isinstance(result, float)
                elif func_name == 'calculate_normalized_entropy':
                    result = func('test')
                    assert isinstance(result, float)
                    assert 0.0 <= result <= 1.0
                elif func_name == 'entropy_category':
                    result = func(3.5, unit='char')
                    assert isinstance(result, str)

                health['functions_working'].append(func_name)
            except Exception as e:
                health['import_error'] = f"{func_name} test failed: {e}"

    except ImportError as e:
        health['import_error'] = f"Import failed: {e}"
    except Exception as e:
        health['import_error'] = f"Unexpected error: {e}"

    return health


def scan_for_usage() -> dict:
    """
    Scan codebase for entropy function usage.

    Returns:
        dict with usage statistics
    """
    usage = {
        'files_using_entropy': [],
        'total_calls_found': 0,
        'timestamp': datetime.now().isoformat()
    }

    # Search for imports and calls
    search_patterns = [
        'calculate_shannon_entropy',
        'calculate_normalized_entropy',
        'entropy_category'
    ]

    # Scan Python files
    for py_file in REPO_ROOT.rglob('*.py'):
        if py_file.name == 'complexity.py':
            continue  # Skip the module itself

        try:
            content = py_file.read_text()
            found = False

            for pattern in search_patterns:
                if pattern in content:
                    usage['total_calls_found'] += content.count(pattern)
                    found = True

            if found:
                usage['files_using_entropy'].append(str(py_file.relative_to(REPO_ROOT)))

        except Exception:
            pass  # Skip files that can't be read

    return usage


def run_monitoring_cycle():
    """
    Run one monitoring cycle.
    """
    global last_check

    print("🔍 Entropy Integration Monitor - Consilium #11")
    print("="*70)
    print(f"Time: {datetime.now().isoformat()}")
    print()

    # Check module health
    print("1️⃣ Checking module health...")
    health = check_module_health()

    if not health['module_exists']:
        print(f"  ✗ Module not found: {COMPLEXITY_MODULE}")
        log_to_resonance(
            "health_check",
            "Module file missing",
            "failed"
        )
        return

    print(f"  ✓ Module exists: {COMPLEXITY_MODULE}")

    if health['functions_present']:
        print(f"  ✓ Functions present: {', '.join(health['functions_present'])}")
    else:
        print(f"  ✗ No entropy functions found")

    if health['functions_working']:
        print(f"  ✓ Functions working: {', '.join(health['functions_working'])}")
    else:
        print(f"  ✗ Functions not working")

    if health['import_error']:
        print(f"  ⚠️ Error: {health['import_error']}")
        log_to_resonance(
            "health_check",
            f"Integration error: {health['import_error']}",
            "failed"
        )
        return

    # Check usage
    print()
    print("2️⃣ Scanning for usage...")
    usage = scan_for_usage()

    if usage['files_using_entropy']:
        print(f"  ✓ Used in {len(usage['files_using_entropy'])} file(s)")
        for file in usage['files_using_entropy']:
            print(f"    - {file}")
    else:
        print(f"  ℹ️ No usage detected yet (expected for new integration)")

    print(f"  ℹ️ Total function calls found: {usage['total_calls_found']}")

    # Log success
    log_to_resonance(
        "monitoring_cycle",
        f"Health: {len(health['functions_working'])}/3 functions working. "
        f"Usage: {usage['total_calls_found']} calls in {len(usage['files_using_entropy'])} files.",
        "success"
    )

    print()
    print("="*70)
    print("✓ Monitoring cycle complete")

    last_check = datetime.now()


def run_daemon(interval_seconds: int = 3600):
    """
    Run monitor as daemon (check every interval_seconds).

    Args:
        interval_seconds: Time between checks (default: 3600 = 1 hour)
    """
    print(f"🛡️ Starting Entropy Integration Monitor daemon")
    print(f"   Interval: {interval_seconds}s ({interval_seconds/3600:.1f}h)")
    print(f"   Consilium: #11")
    print()

    while True:
        try:
            run_monitoring_cycle()
            print(f"\n💤 Sleeping for {interval_seconds}s...")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n⚡ Monitor stopped")
            break
        except Exception as e:
            print(f"\n❌ Error in monitoring cycle: {e}")
            log_to_resonance(
                "monitoring_error",
                str(e),
                "failed"
            )
            time.sleep(60)  # Wait 1 min before retry


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
        run_daemon(interval)
    else:
        run_monitoring_cycle()
