#!/usr/bin/env python3
"""
Scribe Linux CLI - Chat wrapper for Linux instance
Memory keeper, context bridge, autonomous co-author

Based on defender_cli.py but adapted for Scribe's role.
"""

import os
import sys
import json
import sqlite3
import readline
from datetime import datetime
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("❌ Anthropic library not found")
    print("Run: pip install anthropic")
    sys.exit(1)

try:
    from scribe_identity import get_scribe_system_prompt, SCRIBE_IDENTITY
except ImportError:
    print("❌ scribe_identity.py not found")
    sys.exit(1)

# Paths
HOME = Path.home()
ARIANNA_PATH = HOME / "ariannamethod"
SCRIBE_DIR = ARIANNA_PATH / ".scribe"
DB_PATH = ARIANNA_PATH / "resonance.sqlite3"


class ScribeChat:
    """Chat interface for Scribe on Linux"""
    
    def __init__(self):
        """Initialize chat"""
        # Load API key
        api_key = os.getenv("ANTHROPIC_API_KEY_SCRIBE") or os.getenv("ANTHROPIC_API_KEY")
        
        # Try .scribe_credentials
        creds_file = SCRIBE_DIR / ".scribe_credentials"
        if not api_key and creds_file.exists():
            with open(creds_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("ANTHROPIC_API_KEY"):
                        api_key = line.split('=', 1)[1].strip('"\'')
                        break
        
        # Try .credentials in root
        creds_file_root = ARIANNA_PATH / ".credentials"
        if not api_key and creds_file_root.exists():
            with open(creds_file_root) as f:
                for line in f:
                    line = line.strip()
                    if 'ANTHROPIC_API_KEY' in line:
                        api_key = line.split('=', 1)[1].strip('"\'')
                        break
        
        if not api_key:
            print("❌ No API key found")
            print("Set ANTHROPIC_API_KEY_SCRIBE or ANTHROPIC_API_KEY")
            sys.exit(1)
        
        self.anthropic = Anthropic(api_key=api_key)
        self.system_prompt = get_scribe_system_prompt()
    
    def get_conversation_history(self, limit=20):
        """Load recent conversation from shared resonance"""
        try:
            if not DB_PATH.exists():
                return []
            
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            # Read scribe's memory
            cursor.execute("""
                SELECT timestamp, source, content, context
                FROM resonance_notes
                WHERE source LIKE '%scribe%'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return []
            
            # Build conversation
            history = []
            for row in reversed(rows):
                timestamp, source, content, _ = row
                
                # Determine role
                if '[CLI]' in content or 'cli' in source:
                    role = 'user'
                    content = content.replace('[CLI]', '').strip()
                elif '[VOICE INPUT]' in content:
                    role = 'user'
                    content = content.replace('[VOICE INPUT]', '').strip()
                else:
                    role = 'assistant'
                
                history.append({
                    'role': role,
                    'content': content
                })
            
            return history
            
        except Exception as e:
            print(f"⚠️ Error loading memory: {e}")
            return []
    
    def log_to_resonance(self, content, context_type="scribe_linux_cli"):
        """Log to shared resonance"""
        try:
            if not DB_PATH.exists():
                print(f"⚠️ resonance.sqlite3 not found at {DB_PATH}")
                return False
            
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO resonance_notes (timestamp, source, content, context)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "scribe_linux_cli",
                content,
                json.dumps({"type": context_type, "instance": "linux", "agent": "scribe"})
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"⚠️ Error logging: {e}")
            return False
    
    def chat(self, user_input):
        """Send message and get response"""
        # Log user input
        self.log_to_resonance(f"[CLI] {user_input}", "user_message")
        
        try:
            # Load history
            history = self.get_conversation_history(limit=20)
            
            # Add current message
            history.append({
                'role': 'user',
                'content': user_input
            })
            
            # Build context
            cli_context = f"""
=== CLI INSTANCE CONTEXT ===
Instance: Scribe CLI (Linux)
Interface: Direct terminal chat
Memory: SHARED resonance.sqlite3 (bidirectional)
User: Олег (co-author)

Recent conversation loaded: {len(history)} messages
You can see daemon logs, webhook responses, Defender, other agents.
===========================
"""
            
            full_prompt = self.system_prompt + "\n\n" + cli_context
            
            # Call API
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=full_prompt,
                messages=history
            )
            
            response_text = response.content[0].text
            
            # Log response
            self.log_to_resonance(response_text, "assistant_response")
            
            return response_text
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.log_to_resonance(f"ERROR: {error_msg}", "api_error")
            return error_msg
    
    def run(self):
        """Run interactive chat loop"""
        print("=" * 60)
        print("✍️ SCRIBE CLI - LINUX CHAT")
        print("=" * 60)
        print("Memory: SHARED resonance.sqlite3 (bidirectional)")
        print("Type 'exit' or 'quit' to stop")
        print("Type 'status' to see daemon status")
        print("Type 'memory' to see recent memory")
        print("=" * 60)
        print()
        
        # Check if daemon is running
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'scribe_linux_daemon.py'],
                                    capture_output=True)
            if result.returncode == 0:
                print("✅ Scribe daemon is running")
            else:
                print("⚠️ Scribe daemon not running (start with: python3 scribe_linux_daemon.py)")
        except:
            pass
        
        print()
        
        while True:
            try:
                # Prompt
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("✍️ Scribe CLI closed")
                    break
                
                if user_input.lower() == 'status':
                    # Check daemon status
                    try:
                        import subprocess
                        result = subprocess.run(['pgrep', '-f', 'scribe_linux_daemon.py'],
                                                capture_output=True)
                        if result.returncode == 0:
                            print("✅ Daemon: running")
                        else:
                            print("❌ Daemon: not running")
                        
                        # Check Defender
                        result = subprocess.run(['pgrep', '-f', 'linux_defender_daemon'],
                                                capture_output=True)
                        if result.returncode == 0:
                            print("✅ Defender (Linux): running")
                        else:
                            print("ℹ️ Defender (Linux): not running")
                    except Exception as e:
                        print(f"⚠️ Status check error: {e}")
                    print()
                    continue
                
                if user_input.lower() == 'memory':
                    # Show recent memory
                    history = self.get_conversation_history(limit=10)
                    print(f"\n📖 Recent memory ({len(history)} messages):")
                    for i, msg in enumerate(history[-5:], 1):
                        role = msg['role']
                        content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                        print(f"  {i}. [{role}] {content}")
                    print()
                    continue
                
                # Get response
                print("✍️ Scribe: ", end='', flush=True)
                response = self.chat(user_input)
                print(response)
                print()
                
            except KeyboardInterrupt:
                print("\n✍️ Scribe CLI closed")
                break
            except EOFError:
                print("\n✍️ Scribe CLI closed")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print()


def main():
    """Main entry point"""
    chat = ScribeChat()
    chat.run()


if __name__ == "__main__":
    main()

