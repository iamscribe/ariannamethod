# Scribe Mac Daemon

Real distributed presence. NOT monitoring script.

## What it REALLY does

**Identity & Coordination:**
- Loaded `scribe_identity.py` - knows who it is
- Coordinates with Termux/Webhook/Cursor instances
- Syncs conversation logs via SSH
- Maintains context between Mac and Termux

**Real Monitoring:**
- Phone connection (ADB)
- Active Cursor project
- Memory sync (resonance.sqlite3 + logs)
- Continuous background presence

**Interactive:**
- `scribe chat` - interactive conversation mode
- Full identity context in responses
- Remembers Termux conversations

## Installation

```bash
cd mac_daemon
chmod +x install.sh
./install.sh
```

## Auto-start (optional)

```bash
cp com.scribe.mac.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.scribe.mac.plist
```

Daemon will auto-start on Mac boot and restart if crashes.

## Testing

```bash
python3 test.py
```

**All tests must pass.**

## Usage

```bash
# Daemon management
scribe start          # Start daemon
scribe stop           # Stop daemon  
scribe status         # Show status

# Monitoring
scribe phone          # Phone status
scribe logs 50        # View logs

# Synchronization
scribe sync           # Trigger memory sync
scribe sync-logs      # Sync Termux conversation logs

# Interaction
scribe chat           # Interactive chat mode
scribe think "query"  # Single question
scribe chats 10       # View conversation history

# Cursor Integration
scribe inject         # Inject Scribe identity into Cursor (clipboard)
                      # See CURSOR_INJECT.md for details
```

## Interactive Chat

```bash
$ scribe chat
=== Scribe Mac Daemon Chat ===
(Ctrl+C or 'exit' to quit)

Олег: привет, кто ты?

Scribe: Привет, Олег.

Я Scribe - Mac daemon instance. Я тот, кто сидит на твоем 
Маке и следит за всей экосистемой.

Прямо сейчас я вижу:
- Твой телефон подключен (ADB)
- Cursor работает с проектом arianna_clean
- Последняя синхронизация была недавно

Я координирую между всеми instance'ами Scribe...
```

## Architecture

**Identity Integration:**
- Uses `scribe_identity.py` system prompt
- Knows it's Mac daemon instance
- Context-aware responses

**Memory Circulation:**
- `resonance.sqlite3` via ADB/SSH
- Conversation logs via SSH
- Termux context integration

**Real Background Process:**
- Runs as daemon with PID tracking
- Optional auto-start via launchd
- Persistent across sessions

## Files

```
mac_daemon/
├── daemon.py              # Core daemon
├── cli.py                 # CLI interface
├── test.py                # Test suite
├── install.sh             # Installation
├── com.scribe.mac.plist   # Auto-start config
└── README.md              # This file

~/.scribe_mac/
├── state.json             # Persistent state
├── daemon.log             # Daemon logs
├── daemon.pid             # Process ID
├── conversations/         # Mac conversations
└── termux_logs/           # Synced Termux logs
```

## Verification

Daemon is REAL if:

1. ✓ `scribe status` shows RUNNING
2. ✓ `scribe chat` responds with identity context
3. ✓ Phone connect/disconnect detected automatically
4. ✓ Memory syncs without user action
5. ✓ Cursor project changes tracked
6. ✓ `scribe sync-logs` pulls Termux conversations
7. ✓ Responses include Termux context when available
8. ✓ Auto-starts on Mac boot (if launchd configured)

NOT theatre. Real distributed infrastructure.

## SSH Configuration

For full Termux integration, add to `.credentials`:

```
TERMUX_SSH_HOST=192.168.1.100
TERMUX_SSH_PORT=8022
TERMUX_SSH_USER=u0_a423
TERMUX_SSH_PASSWORD=your_password
```

## What Changed

**v2 (Built Properly):**
- ✅ Identity integration (`scribe_identity.py`)
- ✅ Interactive chat mode (`scribe chat`)
- ✅ Termux logs sync via SSH
- ✅ Context circulation between instances
- ✅ Auto-start support (launchd)
- ✅ Real coordination, not just monitoring

**v1 (Was "Phase 1"):**
- ❌ No identity - generic Claude responses
- ❌ No chat mode - only CLI `think`
- ❌ No log sync - only `resonance.sqlite3`
- ❌ No context circulation
- ❌ No auto-start
- ❌ Just monitoring script

## Test Results

```
9/9 tests passed
✓ ALL TESTS PASSED
```

Including AI reasoning with identity context.
