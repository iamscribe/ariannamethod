#!/usr/bin/env python3
"""
Consilium Integration Daemon
Checks quarantine status daily and auto-integrates approved code

AUTONOMOUS WORKFLOW:
- Every 6 hours: check all sandboxes in quarantine
- If quarantine period over + tests passed → AUTO-INTEGRATE
- If tests failed → rollback and notify
- Notifications: "🔬 In quarantine" / "✅ Integrated" / "❌ Failed"

Tower built one floor higher.
"""

import time
import sys
from pathlib import Path
from datetime import datetime

# Add path for sandbox manager
sys.path.insert(0, str(Path(__file__).parent))

from consilium_sandbox_manager import ConsiliumSandboxManager

CHECK_INTERVAL = 6 * 3600  # 6 hours


def send_notification(title: str, content: str, priority: str = "default"):
    """Send Termux notification"""
    try:
        import subprocess
        subprocess.run([
            "termux-notification",
            "--title", title,
            "--content", content,
            "--priority", priority
        ], capture_output=True, timeout=10)
    except:
        print(f"📱 [{title}] {content}")


def check_and_integrate_ready_sandboxes():
    """Check all sandboxes and integrate those ready"""
    manager = ConsiliumSandboxManager()
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking sandboxes...")
    print("=" * 60)
    
    active_sandboxes = manager.list_active_sandboxes()
    
    if not active_sandboxes:
        print("→ No active sandboxes")
        return
    
    print(f"Found {len(active_sandboxes)} active sandbox(es)")
    
    for sandbox in active_sandboxes:
        sandbox_id = sandbox['id']
        repo_name = sandbox['repo_name']
        
        print(f"\n🔬 Checking: {repo_name} (ID: {sandbox_id})")
        
        # Check quarantine status
        status = manager.check_quarantine_status(sandbox_id)
        
        if status.get('ready'):
            tests_passed = status.get('tests_passed', False)
            
            if tests_passed and status.get('can_integrate'):
                print(f"✅ Quarantine complete, tests passed → INTEGRATING")
                
                # Auto-integrate!
                result = manager.integrate_from_sandbox(sandbox_id)
                
                if 'error' not in result:
                    # Success!
                    send_notification(
                        "✅ Code Integrated",
                        f"Repository: {repo_name}\nAuto-integrated after 48h quarantine\nAll tests passed",
                        priority="high"
                    )
                    
                    # Cleanup sandbox
                    manager.cleanup_sandbox(sandbox_id)
                    
                    print(f"   ✅ Successfully integrated and cleaned up")
                else:
                    send_notification(
                        "❌ Integration Failed",
                        f"Repository: {repo_name}\nError: {result['error']}",
                        priority="high"
                    )
                    print(f"   ❌ Integration failed: {result['error']}")
            else:
                # Tests failed
                print(f"❌ Quarantine complete, but tests FAILED")
                
                send_notification(
                    "❌ Quarantine Failed",
                    f"Repository: {repo_name}\nTests failed, code NOT integrated",
                    priority="high"
                )
                
                # Mark as failed (don't integrate)
                # Sandbox stays for manual review
        else:
            time_left = status.get('time_left_hours', 0)
            print(f"⏳ Still in quarantine ({time_left:.1f} hours left)")
    
    print("=" * 60)


def daemon_mode():
    """Run as daemon - check every 6 hours"""
    print("=" * 60)
    print("🔬 CONSILIUM INTEGRATION DAEMON")
    print("=" * 60)
    print("Checking quarantine status every 6 hours")
    print("Auto-integrating code that passes tests")
    print("=" * 60)
    print()
    
    while True:
        try:
            check_and_integrate_ready_sandboxes()
            
            print(f"\n💤 Next check in 6 hours...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n⏹️ Daemon stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(3600)  # Wait 1 hour on error


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        daemon_mode()
    else:
        # One-time check
        check_and_integrate_ready_sandboxes()

