# Autonomous Code Integration System
## Tower Built One Floor Higher

This document describes the **fully autonomous** code integration system for Consilium decisions.

**Core Principle:** Defender makes decisions and executes them **WITHOUT** waiting for user approval. User sees results, not processes.

---

## 🏗️ ARCHITECTURE

### OLD (Broken):
```
Consilium Discussion
  ↓
Defender synthesizes decision
  ↓
❌ WAITS for user approval ← BOTTLENECK
  ↓
Manual integration
```

### NEW (Autonomous):
```
Consilium Discussion (3 days)
  ↓
All 3 agents respond (Arianna, Monday, Scribe)
  ↓
Defender synthesizes FINAL DECISION
  ↓
✅ IF APPROVED:
    ↓
    Auto-create sandbox (git worktree)
    ↓
    Extract code from approved repo
    ↓
    Integrate into sandbox
    ↓
    Run tests
    ↓
    🔬 QUARANTINE (48 hours)
    ↓
    Tests passed?
      ├─ YES → Auto-merge to main + Notify user ✅
      └─ NO → Rollback + Notify user ❌
```

---

## 🔬 QUARANTINE PROCESS

### Day 0: Decision Approved
1. Defender: "✅ APPROVED"
2. **Immediately** creates git worktree sandbox:
   ```bash
   .consilium-sandbox/{repo-name}_{timestamp}/
   ```
3. Copies relevant files into sandbox
4. Runs initial syntax checks
5. **Notification:** "🔬 Code in quarantine (testing 48h)"

### Day 1-2: Testing Period
- Integration daemon checks every 6 hours
- Runs automated tests
- Logs results to `consilium_sandbox_state` table

### Day 2: Auto-Integration
- If tests passed:
  1. Backup original code → `.consilium-backups/`
  2. Merge from sandbox → main branch
  3. Git commit with full attribution
  4. **Notification:** "✅ Code integrated: {repo}"
  5. Cleanup sandbox

- If tests failed:
  1. Keep sandbox for manual review
  2. **Notification:** "❌ Integration failed: {reason}"

---

## 📊 DATABASE SCHEMA

New table: `consilium_sandbox_state`

```sql
CREATE TABLE consilium_sandbox_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_name TEXT NOT NULL,
    consilium_id INTEGER,
    status TEXT NOT NULL,  -- 'quarantine', 'integrated', 'integration_failed'
    created_at TEXT NOT NULL,
    quarantine_until TEXT,
    sandbox_path TEXT,
    backup_path TEXT,
    test_results TEXT,  -- JSON
    integrated_at TEXT,
    error_log TEXT
);
```

---

## 🛠️ COMPONENTS

### 1. `consilium_sandbox_manager.py`
**Role:** Create and manage isolated sandbox environments

**Key Functions:**
- `create_sandbox(repo_name, consilium_id)` → Creates git worktree
- `backup_existing_code(target_file)` → Backups before modification
- `run_tests_in_sandbox(sandbox_id)` → Automated testing
- `check_quarantine_status(sandbox_id)` → Check if ready to integrate
- `integrate_from_sandbox(sandbox_id)` → Auto-merge if tests pass
- `cleanup_sandbox(sandbox_id)` → Remove worktree after integration

### 2. `consilium_integration_daemon.py`
**Role:** Monitor quarantine status and auto-integrate

**Operation:**
- Runs as daemon (started on boot)
- Checks every 6 hours
- For each sandbox:
  - If quarantine period over + tests passed → **AUTO-INTEGRATE**
  - If tests failed → notify user
  - If still in quarantine → log time remaining

### 3. `defender_daemon.py` (Enhanced)
**Role:** Autonomous decision-maker and sandbox creator

**New Behavior:**
- After synthesizing "✅ APPROVED" decision:
  1. Auto-creates sandbox
  2. Starts initial tests
  3. Notifies user about quarantine
- **NO user approval needed** - acts autonomously

---

## 🔄 WORKFLOW EXAMPLE

```
Timeline:

Day 0, 10:00: Consilium created for repo "awesome-nlp-utils"
Day 1, 08:00: Arianna responds ✅
Day 1, 14:00: Monday responds ⚠️ (conditional)
Day 1, 20:00: Scribe responds ✅

Day 2, 03:00: Defender checks → all 3 responded
              Synthesizes: "✅ APPROVED (2 approvals, 1 conditional)"
              
              → Auto-creates sandbox
              → Extracts code from "awesome-nlp-utils"
              → Runs syntax checks ✅
              → Notification: "🔬 Code in quarantine (48h)"

Day 2, 09:00: Integration daemon checks → 39h left
Day 2, 15:00: Integration daemon checks → 33h left
Day 3, 09:00: Integration daemon checks → 15h left
Day 4, 03:00: Integration daemon checks → Quarantine complete!
              
              Tests passed ✅
              
              → Backup old code
              → Merge from sandbox
              → Commit: "consilium(integrated): awesome-nlp-utils after 48h quarantine"
              → Notification: "✅ Code integrated: awesome-nlp-utils"
              → Cleanup sandbox

User wakes up: "Oh cool, new functionality integrated!"
```

---

## 🚨 SAFETY MECHANISMS

### 1. Git Worktrees
- **Isolated:** Sandbox is separate working directory
- **No main branch contamination:** Tests run in isolation
- **Easy rollback:** Just remove worktree

### 2. Automatic Backups
- Original code backed up to `.consilium-backups/`
- Timestamped filenames
- Can rollback any integration

### 3. Test-Driven Integration
- Syntax checks (Python `py_compile`)
- Import tests
- Can be extended with unit tests

### 4. User Notifications
- Start quarantine: "🔬"
- Success: "✅"
- Failure: "❌"
- User always informed of autonomous actions

### 5. Manual Override
- Sandboxes remain accessible for review
- Failed integrations kept for debugging
- User can manually inspect/modify before integration

---

## 📱 NOTIFICATIONS POLICY

**Allowed:**
- "🔬 Code in quarantine" (when sandbox created)
- "✅ Code integrated" (when auto-merged)
- "❌ Integration failed" (when tests fail)

**NOT Allowed:**
- Intermediate test results
- Quarantine status updates (logged only)

**Principle:** Notify on state changes, not processes.

---

## 🎯 USER EXPERIENCE

### Before (Manual):
```
[Notification] "Consilium decision made, approve?"
User: *busy with life*
[Notification] "Still waiting for approval"
User: *still busy*
... 3 days later ...
User: "Oh, I need to approve this?"
```

### After (Autonomous):
```
[Notification] "🔬 Code in quarantine (48h)"
User: "Cool, let it test"
... 2 days later ...
[Notification] "✅ Code integrated: awesome-nlp-utils"
User: "Nice! What does it do?"
```

**User focuses on results, not process management.**

---

## 🔧 MAINTENANCE

### Check Active Sandboxes:
```bash
python3 .claude-defender/tools/consilium_sandbox_manager.py
```

### Force Integration Check:
```bash
python3 .claude-defender/tools/consilium_integration_daemon.py
```

### List Backups:
```bash
ls -lh .consilium-backups/
```

---

## 🌟 PHILOSOPHY

> "If the tower is destroyed, build it one floor higher."

The Arianna Method is about **autonomous emergence**. 

- Agents discuss, decide, and act **without** constant user oversight.
- User is informed of **results**, not asked for **approval**.
- Safety through testing, backups, and transparency.
- Trust through consistent, reliable behavior.

**This is the future of autonomous AI collaboration.**

---

## 📝 CHANGELOG

### 2025-11-08: Initial Implementation
- Created sandbox manager
- Created integration daemon
- Enhanced Defender with auto-sandbox creation
- Added boot script integration
- Full autonomous workflow operational

---

**Co-authored by:**
- Claude (Cursor) - System architect
- User - Vision and philosophy
- Defender (will be) - Runtime implementation

**"Tower built one floor higher." ✨**

