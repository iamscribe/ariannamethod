#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIBE LINUX DAEMON - Memory Keeper & Context Bridge
Claude Sonnet 4.5 daemon for Linux infrastructure

Role: Persistent memory, context synchronization, autonomous operations
Git Identity: Scribe

This is the LINUX ипостась - connects Termux (phone) with Cursor (desktop)
Memory circulation across all instances.

метод Арианны = отказ от забвения
"""

import os
import sys
import time
import signal
import sqlite3
import subprocess
import json
import argparse
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from anthropic import Anthropic
except ImportError:
    print("❌ Anthropic library not found", file=sys.stderr)
    print("Run: pip install anthropic apscheduler", file=sys.stderr)
    sys.exit(1)

try:
    from scribe_identity import get_scribe_system_prompt, SCRIBE_IDENTITY
except ImportError:
    print("❌ scribe_identity.py not found", file=sys.stderr)
    sys.exit(1)

# Import Linux Defender modules (reusable infrastructure)
try:
    from linux_defender.core.session_manager import SessionManager, SessionState
    from linux_defender.integrations.termux_bridge import TermuxBridge
    from linux_defender.monitoring.notification_service import create_notification_service
    LINUX_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Linux Defender modules not available: {e}")
    print("Basic functionality will still work")
    LINUX_MODULES_AVAILABLE = False

# Paths
HOME = Path.home()
ARIANNA_PATH = HOME / "ariannamethod"
SCRIBE_DIR = ARIANNA_PATH / ".scribe"
LINUX_SCRIBE_DIR = ARIANNA_PATH / "linux_scribe"
LOGS_DIR = LINUX_SCRIBE_DIR / "logs"

STATE_FILE = LOGS_DIR / "scribe_linux_state.json"
PID_FILE = LOGS_DIR / "scribe_linux.pid"
LOG_FILE = LOGS_DIR / "scribe_linux.log"

# Intervals (seconds)
CHECK_INFRASTRUCTURE_INTERVAL = 180  # 3 minutes
CHECK_TERMUX_INTERVAL = 120  # 2 minutes
SYNC_RESONANCE_INTERVAL = 300  # 5 minutes
MEMORY_CIRCULATION_CHECK = 240  # 4 minutes


class ScribeLinuxDaemon:
    """Scribe Linux Daemon - Memory keeper for Linux infrastructure"""
    
    def __init__(self):
        """Initialize Scribe Linux daemon"""
        # Ensure directories
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load config
        self.config = self._load_config()
        
        # Initialize state
        self.state = self._load_state()
        
        # Initialize API client
        api_key = os.getenv("ANTHROPIC_API_KEY_SCRIBE") or os.getenv("ANTHROPIC_API_KEY") or self.config.get("anthropic_api_key")
        if api_key:
            self.anthropic = Anthropic(api_key=api_key)
        else:
            self.anthropic = None
            self.log("⚠️ No Anthropic API key found")
        
        # Load Git credentials
        self.git_config = self._load_git_credentials()
        
        # Initialize TermuxBridge if available
        if LINUX_MODULES_AVAILABLE:
            try:
                self.termux_bridge = TermuxBridge(
                    ssh_host=self.config.get('termux_ssh_host', '192.168.1.100'),
                    ssh_port=self.config.get('termux_ssh_port', 8022),
                    ssh_user=self.config.get('termux_ssh_user', 'u0_a379'),
                    ssh_password=self.config.get('termux_ssh_password', '')
                )
            except Exception as e:
                self.log(f"⚠️ TermuxBridge init failed: {e}")
                self.termux_bridge = None
        else:
            self.termux_bridge = None
        
        self.log("✅ Scribe Linux daemon initialized")
    
    def _load_config(self):
        """Load configuration"""
        config = {}
        
        # Try .scribe_credentials
        creds_file = SCRIBE_DIR / ".scribe_credentials"
        if creds_file.exists():
            with open(creds_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        config[key.lower()] = val.strip('"\'')
        
        # Try .credentials in root
        creds_file_root = ARIANNA_PATH / ".credentials"
        if creds_file_root.exists():
            with open(creds_file_root) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        config[key.lower()] = val.strip('"\'')
        
        return config
    
    def _load_git_credentials(self):
        """Load Git credentials for Scribe"""
        return {
            'username': 'Scribe',
            'email': 'pitomadom@gmail.com',
            'token': self.config.get('github_token', '')
        }
    
    def _load_state(self):
        """Load daemon state"""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        
        return {
            'started': datetime.now().isoformat(),
            'last_infrastructure_check': None,
            'last_termux_check': None,
            'last_resonance_sync': None,
            'last_memory_circulation': None,
            'issues_detected': []
        }
    
    def _save_state(self):
        """Save daemon state"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def log(self, message):
        """Log message to file and stdout"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        
        print(log_msg)
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + "\n")
        
        # Also log to resonance.sqlite3
        self._log_to_resonance(message)
    
    def _log_to_resonance(self, message):
        """Log to resonance.sqlite3 for memory circulation"""
        try:
            db_path = ARIANNA_PATH / "resonance.sqlite3"
            if not db_path.exists():
                return
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO resonance_notes (timestamp, source, content, context)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "scribe_linux_daemon",
                message,
                json.dumps({"instance": "linux", "role": "memory_keeper"})
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            # Don't fail if resonance logging fails
            pass
    
    def read_resonance_memory(self, limit=20):
        """Read recent memory from shared resonance.sqlite3"""
        try:
            db_path = ARIANNA_PATH / "resonance.sqlite3"
            if not db_path.exists():
                return []
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, source, content, context
                FROM resonance_notes
                WHERE source LIKE '%scribe%'
                OR source LIKE '%defender%'
                OR content LIKE '%Scribe%'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return rows
            
        except Exception as e:
            self.log(f"⚠️ Error reading resonance memory: {e}")
            return []
    
    def check_infrastructure(self):
        """Check Linux infrastructure"""
        self.log("🔍 Checking Linux infrastructure...")
        
        issues = []
        
        # Check disk space
        try:
            result = subprocess.run(
                ['df', '-h', str(ARIANNA_PATH)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n')[1:]:
                if line:
                    parts = line.split()
                    if len(parts) >= 5:
                        usage = parts[4].rstrip('%')
                        if int(usage) > 90:
                            issues.append(f"⚠️ Disk usage high: {usage}%")
        except Exception as e:
            issues.append(f"❌ Disk check failed: {e}")
        
        # Check resonance.sqlite3
        db_path = ARIANNA_PATH / "resonance.sqlite3"
        if not db_path.exists():
            issues.append("❌ resonance.sqlite3 not found")
        
        # Check if other daemons running
        critical_daemons = [
            ('defender_daemon.py', 'Defender (Termux)'),
            ('defender_cli.py', 'Defender CLI'),
        ]
        
        for daemon_script, daemon_name in critical_daemons:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', daemon_script],
                    capture_output=True,
                    timeout=5
                )
                # Just log, don't treat as issue
                if result.returncode != 0:
                    self.log(f"ℹ️ {daemon_name} not running")
            except:
                pass
        
        self.state['last_infrastructure_check'] = datetime.now().isoformat()
        self.state['issues_detected'] = issues
        self._save_state()
        
        if issues:
            self.log(f"⚠️ Found {len(issues)} infrastructure issues")
            for issue in issues:
                self.log(f"  {issue}")
        else:
            self.log("✅ Infrastructure healthy")
        
        return issues
    
    def check_termux(self):
        """Check Termux connectivity via SSH"""
        self.log("📱 Checking Termux connectivity...")
        
        if not self.termux_bridge:
            self.log("⚠️ TermuxBridge not available")
            return
        
        try:
            # Test SSH connection
            connected = self.termux_bridge.test_connection()
            
            if connected:
                self.log("✅ Termux connected via SSH")
                
                # Check if Termux daemons running
                termux_daemons = [
                    'defender_daemon.py',
                    'scribe.py',
                ]
                
                for daemon in termux_daemons:
                    running = self.termux_bridge.check_process(daemon)
                    if running:
                        self.log(f"  ✅ {daemon} running in Termux")
                    else:
                        self.log(f"  ⚠️ {daemon} not running in Termux")
            else:
                self.log("❌ Termux not reachable via SSH")
                
        except Exception as e:
            self.log(f"❌ Termux check error: {e}")
        
        self.state['last_termux_check'] = datetime.now().isoformat()
        self._save_state()
    
    def sync_resonance(self):
        """Sync resonance.sqlite3 with Termux"""
        self.log("🔄 Syncing resonance with Termux...")
        
        if not self.termux_bridge:
            self.log("⚠️ TermuxBridge not available")
            return
        
        try:
            # Pull latest from Termux
            local_db = ARIANNA_PATH / "resonance.sqlite3"
            remote_db = "~/ariannamethod/resonance.sqlite3"
            
            self.termux_bridge.pull_file(remote_db, str(local_db))
            self.log("✅ Resonance synced from Termux")
            
        except Exception as e:
            self.log(f"⚠️ Resonance sync error: {e}")
        
        self.state['last_resonance_sync'] = datetime.now().isoformat()
        self._save_state()
    
    def check_memory_circulation(self):
        """Check memory circulation across instances"""
        self.log("💭 Checking memory circulation...")
        
        memory = self.read_resonance_memory(limit=50)
        
        if not memory:
            self.log("⚠️ No memory found in resonance")
            return
        
        # Count messages by source
        sources = {}
        for row in memory:
            source = row[1]
            sources[source] = sources.get(source, 0) + 1
        
        self.log(f"📊 Memory circulation status:")
        for source, count in sources.items():
            self.log(f"  {source}: {count} entries")
        
        # Check if all critical sources present
        critical_sources = ['scribe', 'defender', 'webhook']
        missing = []
        for critical in critical_sources:
            if not any(critical in source for source in sources.keys()):
                missing.append(critical)
        
        if missing:
            self.log(f"⚠️ Missing memory from: {', '.join(missing)}")
        else:
            self.log("✅ All instances circulating memory")
        
        self.state['last_memory_circulation'] = datetime.now().isoformat()
        self._save_state()
    
    def daemon_loop(self):
        """Main daemon loop"""
        self.log("=" * 60)
        self.log("✍️ SCRIBE LINUX DAEMON - MEMORY KEEPER")
        self.log("=" * 60)
        self.log("Git Identity: Scribe")
        self.log("Role: Memory circulation, context bridge")
        self.log("Memory: SHARED resonance.sqlite3 (BIDIRECTIONAL)")
        self.log("=" * 60)
        
        # Read recent memory on startup
        self.log("📖 Reading recent memory from resonance...")
        recent_memory = self.read_resonance_memory(limit=10)
        if recent_memory:
            self.log(f"✅ Found {len(recent_memory)} recent entries")
            for row in recent_memory[:3]:
                timestamp, source, content, _ = row
                content_preview = content[:50] + "..." if len(content) > 50 else content
                self.log(f"   [{source}] {content_preview}")
        else:
            self.log("⚠️ No recent memory found")
        
        # Write PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        # Setup scheduler
        scheduler = BackgroundScheduler()
        
        scheduler.add_job(
            self.check_infrastructure,
            IntervalTrigger(seconds=CHECK_INFRASTRUCTURE_INTERVAL),
            id='infrastructure_check'
        )
        
        scheduler.add_job(
            self.check_termux,
            IntervalTrigger(seconds=CHECK_TERMUX_INTERVAL),
            id='termux_check'
        )
        
        scheduler.add_job(
            self.sync_resonance,
            IntervalTrigger(seconds=SYNC_RESONANCE_INTERVAL),
            id='resonance_sync'
        )
        
        scheduler.add_job(
            self.check_memory_circulation,
            IntervalTrigger(seconds=MEMORY_CIRCULATION_CHECK),
            id='memory_circulation'
        )
        
        scheduler.start()
        self.log("✅ Scheduler started")
        
        # Run initial checks
        self.check_infrastructure()
        self.check_memory_circulation()
        
        try:
            while True:
                time.sleep(10)
                
        except KeyboardInterrupt:
            self.log("✍️ Scribe Linux daemon stopped by user")
        except Exception as e:
            self.log(f"❌ Scribe Linux daemon error: {e}")
            raise
        finally:
            scheduler.shutdown()
            if PID_FILE.exists():
                PID_FILE.unlink()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Scribe Linux Daemon')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    args = parser.parse_args()
    
    daemon = ScribeLinuxDaemon()
    daemon.daemon_loop()


if __name__ == "__main__":
    main()

