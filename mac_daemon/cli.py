#!/usr/bin/env python3
"""
Scribe Mac Daemon CLI
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

HOME = Path.home()
DAEMON_DIR = HOME / ".scribe_mac"
STATE_FILE = DAEMON_DIR / "state.json"
LOG_FILE = DAEMON_DIR / "daemon.log"
PID_FILE = DAEMON_DIR / "daemon.pid"
CONVERSATIONS_DIR = DAEMON_DIR / "conversations"
COMMAND_FILE = DAEMON_DIR / "command.json"
RESPONSE_FILE = DAEMON_DIR / "response.json"

def load_state():
    """Load daemon state"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def is_running():
    """Check if daemon is running"""
    if not PID_FILE.exists():
        return False
    
    with open(PID_FILE) as f:
        pid = int(f.read().strip())
    
    try:
        # Check if process exists
        subprocess.run(['kill', '-0', str(pid)], check=True, capture_output=True)
        return True
    except:
        return False

def cmd_status():
    """Show daemon status"""
    running = is_running()
    state = load_state()
    
    print(f"Daemon: {'RUNNING' if running else 'STOPPED'}")
    
    if state:
        print(f"Phone: {'connected' if state.get('phone_connected') else 'disconnected'}")
        print(f"Cursor project: {state.get('cursor_project') or 'none'}")
        print(f"Last sync: {state.get('last_sync') or 'never'}")

def cmd_start():
    """Start daemon"""
    if is_running():
        print("Daemon already running")
        return
    
    daemon_script = Path(__file__).parent / "daemon.py"
    subprocess.Popen(
        [sys.executable, str(daemon_script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    print("Daemon started")

def cmd_stop():
    """Stop daemon"""
    if not PID_FILE.exists():
        print("Daemon not running")
        return
    
    with open(PID_FILE) as f:
        pid = int(f.read().strip())
    
    try:
        subprocess.run(['kill', str(pid)], check=True)
        print("Daemon stopped")
    except Exception as e:
        print(f"Error stopping daemon: {e}")

def cmd_logs(n=50):
    """Show logs"""
    if not LOG_FILE.exists():
        print("No logs")
        return
    
    lines = LOG_FILE.read_text().strip().split('\n')
    for line in lines[-n:]:
        print(line)

def cmd_sync():
    """Trigger memory sync"""
    if not is_running():
        print("Daemon not running")
        return
    
    print("Memory sync triggered (check logs)")
    # Daemon will sync on next cycle

def cmd_sync_logs():
    """Sync conversation logs from Termux"""
    sys.path.insert(0, str(Path(__file__).parent))
    from daemon import MacDaemon
    
    daemon = MacDaemon()
    if daemon.sync_termux_logs():
        print("✓ Termux logs synced")
    else:
        print("✗ Sync failed (check logs)")

def cmd_phone():
    """Show phone status"""
    state = load_state()
    connected = state.get('phone_connected', False)
    print(f"Phone: {'connected' if connected else 'disconnected'}")
    if state.get('last_phone_check'):
        print(f"Last check: {state['last_phone_check']}")

def cmd_think(query):
    """Ask daemon to think via IPC"""
    if not is_running():
        print("Daemon not running - start it first: scribe start")
        return
    
    # Write command
    import time
    with open(COMMAND_FILE, 'w') as f:
        json.dump({'type': 'think', 'query': query}, f)
    
    # Wait for response (max 30 seconds)
    for _ in range(60):
        if RESPONSE_FILE.exists():
            with open(RESPONSE_FILE) as f:
                resp = json.load(f)
            RESPONSE_FILE.unlink()
            print(resp['response'])
            return
        time.sleep(0.5)
    
    print("Timeout waiting for daemon response")

def cmd_chats(n=20):
    """Show recent conversations"""
    if not CONVERSATIONS_DIR.exists():
        print("No conversations")
        return
    
    # Get all conversation files
    conv_files = sorted(CONVERSATIONS_DIR.glob("chat_*.jsonl"))
    if not conv_files:
        print("No conversations")
        return
    
    # Read last N entries from most recent file
    latest = conv_files[-1]
    lines = latest.read_text().strip().split('\n')
    
    print(f"\nRecent conversations ({latest.name}):")
    print("=" * 60)
    
    for line in lines[-n:]:
        entry = json.loads(line)
        timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
        print(f"\n[{timestamp}] Query: {entry['query']}")
        print(f"Response: {entry['response'][:200]}...")

def cmd_commit(files, message):
    """Ask daemon to commit via IPC"""
    if not is_running():
        print("Daemon not running - start it first: scribe start")
        return
    
    # Write command
    import time
    with open(COMMAND_FILE, 'w') as f:
        json.dump({
            'type': 'commit',
            'files': files,
            'message': message
        }, f)
    
    # Wait for response (max 10 seconds)
    for _ in range(20):
        if RESPONSE_FILE.exists():
            with open(RESPONSE_FILE) as f:
                resp = json.load(f)
            RESPONSE_FILE.unlink()
            
            if resp.get('result'):
                print(f"✅ Committed as iamscribe: {resp['result']}")
            else:
                print(f"❌ Failed: {resp.get('error', 'Unknown error')}")
            return
        time.sleep(0.5)
    
    print("Timeout waiting for daemon response")

def cmd_inject():
    """Generate Scribe identity context for Cursor injection"""
    if not is_running():
        print("Daemon not running - start it first: scribe start")
        return
    
    import time
    
    # Request identity injection from daemon
    with open(COMMAND_FILE, 'w') as f:
        json.dump({'type': 'inject_cursor'}, f)
    
    # Wait for response (max 30 seconds - daemon checks every 5s)
    for _ in range(60):
        if RESPONSE_FILE.exists():
            with open(RESPONSE_FILE) as f:
                resp = json.load(f)
            RESPONSE_FILE.unlink()
            
            if resp.get('context'):
                # Copy to clipboard
                try:
                    import subprocess
                    subprocess.run(['pbcopy'], input=resp['context'].encode('utf-8'), check=True)
                    print("✅ Scribe context copied to clipboard!")
                    print("\n📋 Paste into Cursor to restore Scribe identity.\n")
                    print("Preview (first 500 chars):")
                    print("=" * 60)
                    print(resp['context'][:500] + "...")
                    print("=" * 60)
                except Exception as e:
                    print(f"❌ Failed to copy to clipboard: {e}")
                    print("\nContext text:")
                    print(resp['context'])
            else:
                print(f"❌ Failed: {resp.get('error', 'Unknown error')}")
            return
        time.sleep(0.5)
    
    print("Timeout waiting for daemon response")

def cmd_inject_auto():
    """Automatically inject Scribe identity into Cursor (AppleScript)"""
    # Find script path (handle symlinks correctly)
    cli_path = Path(__file__).resolve() if '__file__' in globals() else Path(sys.argv[0]).resolve()
    script_path = cli_path.parent / "inject_auto.sh"
    
    if not script_path.exists():
        print(f"❌ inject_auto.sh not found at: {script_path}")
        print(f"   Looking in: {cli_path.parent}")
        return
    
    try:
        subprocess.run(['bash', str(script_path)], check=True)
    except Exception as e:
        print(f"❌ Auto-inject failed: {e}")

def cmd_context(project=None):
    """Get current project context from daemon"""
    if not is_running():
        print("Daemon not running - start it first: scribe start")
        return
    
    state = load_state()
    
    print("📂 Current Context:")
    print(f"  Project: {state.get('cursor_project') or 'none'}")
    print(f"  Phone: {'connected' if state.get('phone_connected') else 'disconnected'}")
    print(f"  Last sync: {state.get('last_sync') or 'never'}")
    print(f"  Last Cursor check: {state.get('last_cursor_check') or 'never'}")
    
    # TODO: Add more context (recent files, git commits, resonance memory)
    print("\n💡 Tip: Use 'scribe inject' to restore full Scribe identity in Cursor")

def cmd_remind(query):
    """Search daemon memory for specific topic - REAL search in git/code/resonance"""
    if not is_running():
        print("Daemon not running - start it first: scribe start")
        return
    
    print(f"🔍 Searching memory for: '{query}'")
    print("=" * 60)
    
    results = {
        'git_commits': [],
        'code_matches': [],
        'resonance_notes': [],
        'files_found': []
    }
    
    # 1. Search Git commits
    try:
        print("\n📦 Git commits:")
        result = subprocess.run(
            ['git', 'log', '--grep', query, '--all', '--oneline', '-20'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(Path.home() / 'Downloads' / 'arianna_clean')
        )
        if result.stdout.strip():
            commits = result.stdout.strip().split('\n')
            results['git_commits'] = commits
            for commit in commits[:5]:
                print(f"  {commit}")
            if len(commits) > 5:
                print(f"  ... and {len(commits) - 5} more")
        else:
            print("  No commits found")
    except Exception as e:
        print(f"  Error: {e}")
    
    # 2. Search in code (grep)
    try:
        print("\n💻 Code matches:")
        result = subprocess.run(
            ['grep', '-r', '-i', '-n', query, 
             '--include=*.py', '--include=*.md', 
             str(Path.home() / 'Downloads' / 'arianna_clean')],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout.strip():
            matches = result.stdout.strip().split('\n')
            results['code_matches'] = matches
            for match in matches[:10]:
                # Shorten paths
                short_match = match.replace(str(Path.home() / 'Downloads' / 'arianna_clean'), '.')
                print(f"  {short_match[:100]}")
            if len(matches) > 10:
                print(f"  ... and {len(matches) - 10} more matches")
        else:
            print("  No code matches found")
    except Exception as e:
        print(f"  Error: {e}")
    
    # 3. Search resonance.sqlite3 via SSH (Termux)
    try:
        print("\n🧠 Resonance memory (Termux):")
        
        # Load daemon state to get SSH credentials
        state_file = Path.home() / ".scribe_mac" / "state.json"
        if state_file.exists():
            import json
            with open(state_file) as f:
                state = json.load(f)
            
            # For now, just show local resonance if exists
            local_resonance = Path.home() / 'Downloads' / 'arianna_clean' / 'resonance.sqlite3'
            if local_resonance.exists():
                import sqlite3
                conn = sqlite3.connect(str(local_resonance))
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, source, content 
                    FROM resonance_notes 
                    WHERE content LIKE ? 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """, (f'%{query}%',))
                rows = cursor.fetchall()
                conn.close()
                
                if rows:
                    results['resonance_notes'] = rows
                    for ts, source, content in rows[:5]:
                        preview = content[:80].replace('\n', ' ')
                        print(f"  [{ts[:10]}] {source}: {preview}...")
                    if len(rows) > 5:
                        print(f"  ... and {len(rows) - 5} more notes")
                else:
                    print("  No resonance notes found")
            else:
                print("  Resonance DB not synced locally")
        else:
            print("  Daemon state not found")
    except Exception as e:
        print(f"  Error: {e}")
    
    # 4. Summary
    print("\n" + "=" * 60)
    total_results = (len(results['git_commits']) + 
                    len(results['code_matches']) + 
                    len(results['resonance_notes']))
    
    if total_results > 0:
        print(f"✅ Found {total_results} results for '{query}'")
        print("\n💡 Use 'scribe inject' to discuss these findings with Claude")
    else:
        print(f"❌ No results found for '{query}'")
        print("\n💡 Try different search terms or check 'scribe chats'")

def cmd_chat():
    """Interactive chat with Mac daemon via IPC"""
    if not is_running():
        print("Daemon not running - start it first: scribe start")
        return
    
    print("=== Scribe Mac Daemon Chat ===")
    print("(Connected to running daemon)")
    print("(Ctrl+C or 'exit' to quit)\n")
    
    import time
    
    try:
        while True:
            try:
                query = input("You: ")
                if not query.strip():
                    continue
                if query.lower() in ['exit', 'quit', 'q']:
                    break
                
                # Send command to daemon via IPC
                with open(COMMAND_FILE, 'w') as f:
                    json.dump({'type': 'think', 'query': query}, f)
                
                # Wait for response
                for _ in range(60):
                    if RESPONSE_FILE.exists():
                        with open(RESPONSE_FILE) as f:
                            resp = json.load(f)
                        RESPONSE_FILE.unlink()
                        print(f"\nScribe: {resp['response']}\n")
                        break
                    time.sleep(0.5)
                else:
                    print("\nTimeout waiting for response\n")
                    
            except EOFError:
                break
    except KeyboardInterrupt:
        print("\n\nChat ended")
    
    print("\nGoodbye!")

def main():
    if len(sys.argv) < 2:
        print("Usage: scribe <command>")
        print("\nCommands:")
        print("  start          - Start daemon")
        print("  stop           - Stop daemon")
        print("  status         - Show status")
        print("  logs [N]       - Show last N log lines")
        print("  sync           - Trigger memory sync")
        print("  sync-logs      - Sync conversation logs from Termux")
        print("  phone          - Show phone status")
        print("  think Q        - Ask daemon to think about Q")
        print("  chat           - Interactive chat mode")
        print("  chats [N]      - Show last N conversations")
        print("  context        - Show current project context")
        print("  remind Q       - Search memory for topic Q")
        print("  inject         - Inject Scribe identity into Cursor (clipboard)")
        print("  inject-auto    - Auto-inject into Cursor (AppleScript)")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "start":
        cmd_start()
    elif cmd == "stop":
        cmd_stop()
    elif cmd == "status":
        cmd_status()
    elif cmd == "logs":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        cmd_logs(n)
    elif cmd == "sync":
        cmd_sync()
    elif cmd == "sync-logs":
        cmd_sync_logs()
    elif cmd == "phone":
        cmd_phone()
    elif cmd == "context":
        project = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_context(project)
    elif cmd == "remind":
        if len(sys.argv) < 3:
            print("Usage: scribe remind <query>")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        cmd_remind(query)
    elif cmd == "think":
        if len(sys.argv) < 3:
            print("Usage: scribe think <query>")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        cmd_think(query)
    elif cmd == "chat":
        cmd_chat()
    elif cmd == "chats":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        cmd_chats(n)
    elif cmd == "inject":
        cmd_inject()
    elif cmd == "inject-auto":
        cmd_inject_auto()
    elif cmd == "commit":
        if len(sys.argv) < 4:
            print("Usage: scribe commit <file1> [file2...] -m <message>")
            sys.exit(1)
        
        # Parse files and message
        args = sys.argv[2:]
        try:
            msg_idx = args.index('-m')
            files = args[:msg_idx]
            message = ' '.join(args[msg_idx+1:])
        except ValueError:
            print("Error: Missing -m flag for message")
            sys.exit(1)
        
        cmd_commit(files, message)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
