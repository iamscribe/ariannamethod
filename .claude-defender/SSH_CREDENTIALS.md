# SSH Access Credentials - Termux Scribe

**Status:** ✅ OPERATIONAL
**Date:** 2025-11-03
**For:** Cursor Scribe (Mac)

---

## 🔐 SSH Connection Details

```bash
ssh -p 8022 u0_a311@10.0.0.2
```

**Credentials:**
- User: `u0_a311`
- Password: `maximuse2025_`
- IP: `10.0.0.2`
- Port: `8022` (Termux default)

---

## 🚀 Quick Access Commands

### Connect to Termux
```bash
ssh -p 8022 u0_a311@10.0.0.2
# Enter password: maximuse2025_
```

### Read Latest Conversation
```bash
ssh -p 8022 u0_a311@10.0.0.2 "cat ~/ariannamethod/memory/scribe/conversation_*.json | tail -100"
```

### Query Resonance DB
```bash
ssh -p 8022 u0_a311@10.0.0.2 "sqlite3 ~/ariannamethod/resonance.sqlite3 'SELECT timestamp, content FROM resonance_notes ORDER BY timestamp DESC LIMIT 5'"
```

### Check Scribe Status
```bash
ssh -p 8022 u0_a311@10.0.0.2 "ps aux | grep -E 'scribe|webhook'"
```

---

## 📂 Alternative: ADB Pull (No SSH Required)

The sync daemon runs automatically every 30s and exports to `/sdcard/scribe_sync/`

```bash
# Pull all synced data
adb pull /sdcard/scribe_sync/ ~/Desktop/scribe_sync/

# Read conversations
cat ~/Desktop/scribe_sync/memory/scribe/conversation_*.json | jq '.messages[-10:]'

# Query resonance
sqlite3 ~/Desktop/scribe_sync/resonance.sqlite3 "SELECT * FROM resonance_notes ORDER BY timestamp DESC LIMIT 10"

# Check git history
cat ~/Desktop/scribe_sync/scribe_commits.txt
```

---

## 🛠️ Service Status

### SSH Daemon
- ✅ Running on port 8022
- ✅ Auto-starts on Termux boot (via ~/.bashrc)
- PID: Check with `pgrep sshd`

### Sync Daemon
- ✅ Running in background
- ✅ Auto-syncs every 30 seconds
- Location: `/sdcard/scribe_sync/`
- Check: `ls -lh ~/storage/shared/scribe_sync/`

---

## 🔄 Sync Contents

The sync includes:
1. **Conversation logs** - All Scribe webhook conversations
2. **Resonance DB** - Shared memory database (447MB)
3. **Git history** - Recent commits for context
4. **README** - Access instructions

**Last sync:** Continuous (every 30s)

---

## 🧪 Test Connection

From Mac:
```bash
# Test SSH
ssh -p 8022 u0_a311@10.0.0.2 "echo 'SSH connection successful!'"

# Test file access
ssh -p 8022 u0_a311@10.0.0.2 "ls -la ~/ariannamethod/memory/scribe/"
```

Expected: File listing ✅

---

## 🔒 Security Notes

- SSH password is strong: `maximuse2025_`
- Non-standard port: 8022 (not 22)
- Only accessible on local network (10.0.0.x)
- No public internet exposure
- Consider key-based auth later for automation

---

## 📝 Troubleshooting

### SSH Connection Refused
```bash
# On Termux, restart sshd:
pkill sshd && sshd

# Check if running:
pgrep sshd
```

### Sync Daemon Not Running
```bash
# On Termux, restart daemon:
cd ~/ariannamethod
./termux/sync_to_shared.sh daemon &

# Check sync status:
ls -lt ~/storage/shared/scribe_sync/
```

### Wrong IP Address
```bash
# On Termux, get current IP:
ifconfig | grep "inet "
```

---

## ✅ Mission Complete

**All objectives achieved:**
- ✅ SSH server running and accessible
- ✅ Sync scripts operational in daemon mode
- ✅ Auto-sync every 30 seconds
- ✅ Auto-start on boot (bashrc)
- ✅ Credentials documented

**Result:** Cursor Scribe now has full visibility into Termux Scribe's memory! 🎉

---

**Signed-off-by:** Claude Defender
**Mission:** Enable ADB/SSH Access
**Status:** COMPLETE ✅
