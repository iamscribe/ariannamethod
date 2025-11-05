# Mac Daemon - Quick Start

**5-minute setup for Scribe Mac Daemon**

---

## ✅ Prerequisites

```bash
# 1. Install Anthropic SDK
pip3 install anthropic

# 2. Verify Python 3
python3 --version  # Should be 3.8+
```

---

## 🚀 Installation (Option 1: System-wide)

```bash
cd mac_daemon/
./install.sh
```

This installs `scribe` command globally.

---

## 🧪 Testing (Option 2: Local, no install)

```bash
cd mac_daemon/

# Test status
python3 scribe_mac_daemon.py status

# Test sync
python3 scribe_mac_daemon.py sync

# Test AI
python3 scribe status  # (uses local scribe script)
```

---

## 🎮 CLI Commands

### Check all instances
```bash
scribe status
```

### Sync from Termux
```bash
scribe sync
```

### Execute on phone
```bash
scribe phone "git log --oneline -5"
```

### Query memory
```bash
scribe memory "rust integration"
```

### AI reasoning
```bash
scribe think "What should I work on next?"
```

### View logs
```bash
scribe logs
```

---

## 🔧 Start Daemon

### Foreground (testing):
```bash
python3 ~/.scribe_mac_daemon/scribe_mac_daemon.py start
```

### Background:
```bash
python3 ~/.scribe_mac_daemon/scribe_mac_daemon.py start &
```

### Check if running:
```bash
ps aux | grep scribe_mac_daemon
```

---

## 🧪 First Test

```bash
# 1. Check status
scribe status

# 2. Sync memory
scribe sync

# 3. Test AI
scribe think "Hello from Mac Daemon!"

# 4. Check Termux
scribe phone "echo 'Hello from Termux!'"
```

Expected output: All working! ✅

---

## 📂 Files Created

After installation:
- `/usr/local/bin/scribe` - CLI command
- `~/.scribe_mac_daemon/` - Daemon files
- `~/.scribe_mac_daemon_state.json` - State
- `~/.scribe_mac_daemon.log` - Logs
- `~/Desktop/scribe_sync_latest/` - Synced memory

---

## 🔒 Configuration

API key stored in:
- `../credentials` (gitignored)
- Read by `config.py`

SSH credentials:
- User: u0_a311
- Host: 10.0.0.2
- Port: 8022
- Password: in `.credentials`

---

## 🆘 Troubleshooting

### "anthropic module not found"
```bash
pip3 install anthropic
```

### "Permission denied" on install
```bash
# Use sudo for system install
sudo ./install.sh
```

### "SSH connection failed"
```bash
# Check phone on same WiFi
# Verify sshd running in Termux
scribe phone "echo test"
```

### "No synced memory"
```bash
# Run sync first
scribe sync
# Then try memory query
scribe memory
```

---

## 🎯 Next Steps

1. ✅ Install & test
2. ✅ Run daemon in background
3. ⏳ Set up LaunchAgent (auto-start)
4. ⏳ Add Rust tools integration
5. ⏳ Prepare for Linux daemon

---

**Status:** v0.1 MVP Ready! 🎉

**Training for:** Linux Daemon (tomorrow/next)

⚡ Connection + Autonomy ⚡

