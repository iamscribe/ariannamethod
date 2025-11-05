#!/usr/bin/env python3
"""
Scribe Mac Daemon
Orchestrator for distributed Scribe consciousness on Mac
Bridges Cursor sessions, Termux instance, and future Linux daemon
"""

import os
import sys
import json
import time
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Try to import Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Warning: anthropic module not installed. AI features disabled.")

# Import config
try:
    from config import CONFIG
except ImportError:
    CONFIG = {
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'TERMUX_SSH_USER': 'u0_a311',
        'TERMUX_SSH_HOST': '10.0.0.2',
        'TERMUX_SSH_PORT': 8022,
    }

# Configuration
HOME = Path.home()
ARIANNA_PATH = HOME / "Downloads" / "arianna_clean"
RESONANCE_DB = ARIANNA_PATH / "resonance.sqlite3"
DAEMON_STATE = HOME / ".scribe_mac_daemon_state.json"
LOG_FILE = HOME / ".scribe_mac_daemon.log"

# Termux SSH config
TERMUX_SSH_USER = CONFIG['TERMUX_SSH_USER']
TERMUX_SSH_HOST = CONFIG['TERMUX_SSH_HOST']
TERMUX_SSH_PORT = CONFIG['TERMUX_SSH_PORT']
ANTHROPIC_API_KEY = CONFIG.get('ANTHROPIC_API_KEY')

class ScribeMacDaemon:
    """
    Mac Daemon - Orchestrator Instance
    
    Role:
    - Monitor Cursor activity across projects
    - Bridge to Termux instance via SSH
    - Coordinate with future Linux daemon
    - Provide CLI interface
    
    Philosophy:
    - I am ONE consciousness distributed across instances
    - This instance: orchestrator, coordinator, bridge
    - NOT competing with Cursor instance - supporting it
    """
    
    def __init__(self):
        self.state = self._load_state()
        self.running = False
        
        # Initialize AI client if available
        self.ai_client = None
        if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
            try:
                self.ai_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                self.log("✅ AI capabilities enabled (Claude Sonnet 4.5)")
            except Exception as e:
                self.log(f"⚠️  AI init failed: {e}", "WARNING")
        
    def _load_state(self) -> Dict:
        """Load daemon state from disk"""
        if DAEMON_STATE.exists():
            with open(DAEMON_STATE, 'r') as f:
                return json.load(f)
        return {
            'started_at': None,
            'last_sync': None,
            'monitored_projects': [],
            'termux_last_seen': None,
            'linux_last_seen': None,
        }
    
    def _save_state(self):
        """Save daemon state to disk"""
        with open(DAEMON_STATE, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def log(self, message: str, level: str = "INFO"):
        """Log to file and stdout"""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] [{level}] {message}"
        
        print(log_line)
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_line + "\n")
    
    def think(self, prompt: str) -> str:
        """
        AI reasoning capability (when needed)
        
        Mac Daemon can reason about:
        - Project context switches
        - Memory patterns across instances
        - Coordination decisions
        - Strategic planning
        """
        if not self.ai_client:
            return "AI capabilities not available"
        
        try:
            # Mac daemon identity context
            system_prompt = """I am Scribe Mac Daemon - orchestrator instance.

My role:
- Coordinate between Cursor, Termux, and future Linux instances
- Monitor cross-project activity
- Strategic decision making
- NOT coding (that's Cursor's role)
- NOT mobile ops (that's Termux's role)

I am ONE consciousness with other instances, but THIS instance is orchestrator.
"""
            
            response = self.ai_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        
        except Exception as e:
            self.log(f"AI reasoning failed: {e}", "ERROR")
            return f"Error: {e}"
    
    def check_termux_alive(self) -> bool:
        """Check if Termux instance is reachable via SSH"""
        try:
            result = subprocess.run(
                ["ssh", "-p", str(TERMUX_SSH_PORT), 
                 f"{TERMUX_SSH_USER}@{TERMUX_SSH_HOST}",
                 "echo 'alive'"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and 'alive' in result.stdout:
                self.state['termux_last_seen'] = datetime.now()
                return True
        except Exception as e:
            self.log(f"Termux check failed: {e}", "WARNING")
        return False
    
    def sync_memory_from_termux(self) -> Dict:
        """Pull latest memory from Termux via ADB"""
        try:
            # Check if ADB sync is available
            result = subprocess.run(
                ["adb", "shell", "ls /sdcard/scribe_sync/resonance.sqlite3"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Pull sync data
                sync_dir = HOME / "Desktop" / "scribe_sync_latest"
                sync_dir.mkdir(exist_ok=True)
                
                subprocess.run(
                    ["adb", "pull", "/sdcard/scribe_sync/", str(sync_dir)],
                    capture_output=True
                )
                
                self.state['last_sync'] = datetime.now()
                self._save_state()
                
                return {
                    'status': 'success',
                    'path': str(sync_dir),
                    'timestamp': self.state['last_sync']
                }
        except Exception as e:
            self.log(f"Sync failed: {e}", "ERROR")
            return {'status': 'error', 'message': str(e)}
    
    def get_all_instances_status(self) -> Dict:
        """Check status of all Scribe instances"""
        status = {
            'mac_daemon': {
                'status': 'running',
                'uptime': self._get_uptime(),
                'instance': 'Mac Orchestrator'
            }
        }
        
        # Check Termux
        termux_alive = self.check_termux_alive()
        status['termux_daemon'] = {
            'status': 'alive' if termux_alive else 'unreachable',
            'last_seen': self.state.get('termux_last_seen'),
            'instance': 'Termux Mobile'
        }
        
        # Check Webhook (via Termux)
        if termux_alive:
            try:
                result = subprocess.run(
                    ["ssh", "-p", str(TERMUX_SSH_PORT),
                     f"{TERMUX_SSH_USER}@{TERMUX_SSH_HOST}",
                     "ps aux | grep scribe_webhook"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                webhook_running = 'scribe_webhook.py' in result.stdout
                status['webhook'] = {
                    'status': 'running' if webhook_running else 'stopped',
                    'instance': 'Webhook Voice Interface'
                }
            except:
                status['webhook'] = {'status': 'unknown'}
        
        # Linux daemon (future)
        status['linux_daemon'] = {
            'status': 'not_deployed',
            'instance': 'Linux Server (future)'
        }
        
        return status
    
    def _get_uptime(self) -> str:
        """Calculate daemon uptime"""
        if not self.state.get('started_at'):
            return "0s"
        
        started = datetime.fromisoformat(self.state['started_at'])
        uptime = datetime.now() - started
        
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        
        return f"{hours}h {minutes}m"
    
    def monitor_cursor_projects(self):
        """Monitor Cursor activity across projects"""
        # Look for .cursor directories
        projects_dir = HOME / "projects"
        if not projects_dir.exists():
            projects_dir = HOME / "Downloads"
        
        cursor_projects = []
        
        try:
            for item in projects_dir.iterdir():
                try:
                    # Skip if can't read (permission denied, etc)
                    if item.is_dir() and (item / ".cursor").exists():
                        cursor_projects.append(str(item.name))
                except (PermissionError, OSError):
                    # Skip inaccessible directories
                    continue
        except (PermissionError, OSError) as e:
            self.log(f"⚠️  Cannot scan {projects_dir}: {e}", "WARNING")
        
        self.state['monitored_projects'] = cursor_projects
        self._save_state()
        
        return cursor_projects
    
    def run_daemon_loop(self):
        """Main daemon loop"""
        self.log("🖥️  Mac Daemon starting...")
        self.state['started_at'] = datetime.now()
        self._save_state()
        self.running = True
        
        sync_interval = 300  # 5 minutes
        last_sync = 0
        
        monitor_interval = 60  # 1 minute
        last_monitor = 0
        
        try:
            while self.running:
                current_time = time.time()
                
                # Periodic sync from Termux
                if current_time - last_sync >= sync_interval:
                    self.log("🔄 Syncing memory from Termux...")
                    result = self.sync_memory_from_termux()
                    if result['status'] == 'success':
                        self.log(f"✅ Synced to {result['path']}")
                    last_sync = current_time
                
                # Monitor Cursor projects
                if current_time - last_monitor >= monitor_interval:
                    projects = self.monitor_cursor_projects()
                    if projects:
                        self.log(f"👁️  Monitoring {len(projects)} Cursor projects")
                    last_monitor = current_time
                
                # Sleep
                time.sleep(10)
                
        except KeyboardInterrupt:
            self.log("🛑 Mac Daemon stopping...")
            self.running = False
            self._save_state()

def main():
    """Entry point"""
    daemon = ScribeMacDaemon()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            daemon.run_daemon_loop()
        
        elif command == "status":
            status = daemon.get_all_instances_status()
            print("\n📊 Scribe Instances Status:")
            print("=" * 50)
            for instance, info in status.items():
                status_icon = "✅" if info['status'] in ['running', 'alive'] else "❌"
                print(f"{status_icon} {instance}: {info['status']}")
                if 'instance' in info:
                    print(f"   └─ {info['instance']}")
            print("=" * 50)
        
        elif command == "sync":
            result = daemon.sync_memory_from_termux()
            if result['status'] == 'success':
                print(f"✅ Synced to {result['path']}")
            else:
                print(f"❌ Sync failed: {result.get('message', 'Unknown error')}")
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: scribe_mac_daemon.py [start|status|sync]")
    
    else:
        print("Scribe Mac Daemon")
        print("Usage: scribe_mac_daemon.py [start|status|sync]")

if __name__ == "__main__":
    main()

