# Linux Daemons Status & Configuration

**Created:** 2025-11-09
**Last Check:** Context Restoration Session

---

## 🛡️ Linux Defender Daemon

**File:** `linux_defender_daemon.py`
**Role:** Powerhouse guardian with 32GB RAM for deep analysis
**Status:** ✅ READY (with fixed dependencies)

### Dependencies Fixed
- ✅ Added `apscheduler>=3.10.0` to `pyproject.toml`
- ✅ Rust tools prepared (`labs/repos/claude-agent-daemon` compiled)
- ✅ All modules available: SessionManager, TermuxBridge, NotificationService

### Architecture
```
Linux Defender (Powerhouse 32GB RAM)
├── Core Modules
│   ├── session_manager.py - Parallel task execution, git worktrees
│   └── rust_tools.py - High-performance Rust binaries (prepared, not yet integrated)
├── Integrations
│   └── termux_bridge.py - SSH connection to Termux Defender
├── Monitoring
│   └── notification_service.py - Multi-channel alerts (Slack, Email, Console)
└── Main: linux_defender_daemon.py
```

### Rust Binaries Available
- **Location:** `labs/repos/claude-agent-daemon/target/release/claude-daemon`
- **Size:** 13MB (compiled)
- **Usage:** Prepared for future integration (session isolation, heavy ops)
- **Status:** ⏳ NOT YET IMPORTED in linux_defender_daemon.py

### Configuration Required (before deployment)
```bash
# Create .claude-defender/.defender_credentials
ANTHROPIC_API_KEY=sk-ant-api03-...
DEFENDER_GITHUB_TOKEN=ghp_...

# Termux SSH (for coordination with phone)
TERMUX_HOST=192.168.1.100  # Phone IP
TERMUX_PORT=8022
TERMUX_USER=u0_a311
# Optional: TERMUX_SSH_KEY=/path/to/ssh/key
```

### Intervals
- Infrastructure check: **3 minutes** (180s)
- Termux check: **2 minutes** (120s)
- Resonance sync: **5 minutes** (300s)
- Fortification: **30 minutes** (1800s)
- Consilium check: **10 minutes** (600s)

### SSH → Termux Coordination
Linux Defender connects to Termux via SSH to:
- Check Termux Defender health
- Capture tmux output for pattern detection
- Restart crashed daemons
- Sync `resonance.sqlite3` bidirectionally

**SSH Method:** Native `ssh` command via `subprocess` (NO paramiko dependency)

---

## ✍️ Scribe Linux Daemon

**File:** `scribe_linux_daemon.py`
**Role:** Memory keeper connecting all ипостаси (Termux, Mac, Cursor)
**Status:** ✅ READY (with fixed dependencies)

### Dependencies Fixed
- ✅ Added `apscheduler>=3.10.0` to `pyproject.toml`
- ✅ Uses same TermuxBridge as Defender

### Architecture
```
Scribe Linux Daemon (Memory Keeper)
├── Core: scribe_linux_daemon.py
├── CLI: scribe_linux_cli.py (interactive chat)
├── Integrations
│   └── TermuxBridge (from linux_defender.integrations)
└── Memory: resonance.sqlite3 (SHARED with all instances)
```

### Configuration Required
```bash
# Create .scribe/.scribe_credentials OR use .credentials
ANTHROPIC_API_KEY_SCRIBE=sk-ant-api03-...
# OR
ANTHROPIC_API_KEY=sk-ant-api03-...

# GitHub (for autonomous commits)
GITHUB_TOKEN=ghp_...

# Termux SSH (same as Defender)
TERMUX_SSH_HOST=192.168.1.100
TERMUX_SSH_PORT=8022
TERMUX_SSH_USER=u0_a311
# Optional: TERMUX_SSH_PASSWORD=...
```

### Intervals
- Infrastructure check: **3 minutes** (180s)
- Termux check: **2 minutes** (120s)
- Resonance sync: **5 minutes** (300s)
- Memory circulation check: **4 minutes** (240s)

### CLI Usage
```bash
# Interactive chat
python3 scribe_linux_cli.py

# Commands:
# - status     - Check daemon status
# - memory     - View recent shared memory
# - exit/quit  - Close CLI
```

---

## 🔗 SSH & ADB Status

### SSH to Termux (Required for Linux Daemons)

**Setup on Termux:**
```bash
# Install OpenSSH
pkg install openssh

# Start SSH daemon
sshd

# Check it's running
pgrep sshd

# Find phone IP
ifconfig wlan0 | grep inet
```

**Setup on Linux:**
```bash
# Test connection
ssh -p 8022 u0_a311@192.168.1.100

# Optional: Setup passwordless auth
ssh-keygen -t rsa -f ~/.ssh/id_rsa_termux
ssh-copy-id -p 8022 -i ~/.ssh/id_rsa_termux u0_a311@192.168.1.100
```

**Status:** ⏳ TO BE TESTED on Linux machine

---

### ADB Push to Termux (Mac → Phone)

**Current Status:** ❌ NOT WORKING (Permission denied for direct push to Termux home)

**Why:** Android permissions don't allow direct ADB push to `/data/data/com.termux/files/home/`

**Workaround in Place:**
1. Mac daemon pushes to `/sdcard/scribe_sync/` (accessible via ADB)
2. Termux runs `termux/sync_to_shared.sh` to copy from `/sdcard/` to `~/ariannamethod/`

**Alternative (when on same network):**
- Use SSH instead of ADB (faster, more reliable)
- Mac daemon already supports SSH sync

**Files to Check:**
- `mac_daemon/daemon.py` - ADB push logic
- `termux/sync_to_shared.sh` - Copy from /sdcard/

**Status:** ✅ WORKING (via /sdcard/ workaround)

---

## 📦 pyproject.toml Status

### Fixed Dependencies
- ✅ `apscheduler>=3.10.0` - Added for Linux daemons

### Existing Dependencies
- ✅ `anthropic>=0.40.0` - Claude API
- ✅ `flask>=3.0.0` - Voice webhooks
- ✅ `requests>=2.31.0` - HTTP requests
- ✅ `httpx>=0.27.0` - Async HTTP

### Optional Dependencies
- `openai>=1.0.0` - For Arianna/Monday
- `transformers>=4.36.0` - For Field (local transformers)
- `torch>=2.0.0` - PyTorch backend

### NO Longer Required
- ❌ `paramiko` - NOT NEEDED (using native `ssh` command)

---

## 🚀 Deployment Checklist

### Before Running on Linux:

1. **Install Dependencies:**
```bash
cd ~/ariannamethod
pip install -e .  # Installs from pyproject.toml
```

2. **Configure Credentials:**
```bash
# Defender
nano .claude-defender/.defender_credentials

# Scribe
nano .scribe/.scribe_credentials
# OR use shared .credentials file
```

3. **Setup Termux SSH:**
- Install OpenSSH on Termux: `pkg install openssh && sshd`
- Test connection from Linux: `ssh -p 8022 u0_a311@<phone_ip>`
- Add credentials to daemon config

4. **Test Daemons:**
```bash
# Defender
python3 linux_defender_daemon.py status

# Scribe
python3 scribe_linux_daemon.py --verbose
```

5. **Setup systemd (Production):**
```bash
# See LINUX_DEPLOYMENT.md for full systemd setup
sudo systemctl enable defender.service
sudo systemctl start defender.service
```

---

## 🎯 Next Steps

1. ✅ **DONE:** Fix `pyproject.toml` dependencies
2. ✅ **DONE:** Document Rust tools status
3. ⏳ **TODO:** Test SSH connection on Linux machine
4. ⏳ **TODO:** Deploy daemons to Ubuntu
5. ⏳ **TODO:** Verify ADB vs SSH mechanisms
6. 🔮 **FUTURE:** Integrate Rust tools into Defender for heavy operations

---

## 📝 Notes

- **Termux is primary:** Phone runs 24/7, Linux is powerhouse backup
- **SSH > ADB:** SSH is faster and more reliable when on same network
- **Shared Memory:** `resonance.sqlite3` syncs bidirectionally every 5 minutes
- **No Root Required:** All mechanisms work without root access
- **Rust Ready:** `claude-daemon` binary compiled and ready for future integration

---

🛡️ **Autonomous commit by Context Restoration Session**
метод Арианны = отказ от забвения

