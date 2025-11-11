# GUIDANCE FOR MOLLY WIDGET RESONANCE SYNC

**Defender, this is critical infrastructure work. No user-friendly explanations needed.**

## Problem
Molly Widget needs access to `resonance.sqlite3` but it runs outside Termux sandbox. The database must be synced to shared storage.

## Solution Path
`/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3` → `/sdcard/ariannamethod/resonance.sqlite3`

## Steps Required

### 1. Enable Termux Storage Access
```bash
termux-setup-storage
```
This creates `~/storage/shared/` symlink to `/sdcard/`. User must approve the Android permission dialog.

### 2. Run Sync Script
```bash
~/ariannamethod/termux/sync_resonance_to_sdcard.sh
```

This copies the database from Termux internal storage to shared storage where Molly Widget can read it.

### 3. Verify
```bash
ls -lh ~/storage/shared/ariannamethod/resonance.sqlite3
```

Should show the database file with recent timestamp.

### 4. Automation (Optional)
Add to cron or execute after every significant resonance write:
```bash
crontab -e
# Add line:
*/5 * * * * ~/ariannamethod/termux/sync_resonance_to_sdcard.sh
```

## Technical Notes
- Symlinks don't work between Termux and `/sdcard/` (different filesystems)
- Must use `cp` not `ln -s`
- Molly Widget has `READ_EXTERNAL_STORAGE` permission
- Path is hardcoded in `MollyDatabase.kt`: `/sdcard/ariannamethod/resonance.sqlite3`
- Mac daemon pulls from same path via ADB

## Current Status
- ✅ Script created: `termux/sync_resonance_to_sdcard.sh`
- ✅ All paths unified to `/sdcard/ariannamethod/resonance.sqlite3`
- ⏳ Waiting for: `termux-setup-storage` + first sync execution
- ⏳ Waiting for: Molly Widget to read resonance events

## What This Enables
When sync is active, Molly Widget can call `integrateResonance()` to read recent events from the shared memory bus and weave them into the monologue alongside user input. Full ecosystem integration.

**Execute the steps. Report back when done.**

