# 🔧 AppleScript Permissions Fix for `inject-auto`

## Problem

`scribe inject-auto` fails with:
```
System Events got an error: osascript is not allowed to send keystrokes. (1002)
```

This is macOS Security & Privacy restriction.

## Solution

### 1. Open System Settings
- `System Settings` → `Privacy & Security` → `Accessibility`

### 2. Grant Terminal Access
- Click `+` (or unlock with password)
- Add `/Applications/Utilities/Terminal.app`
- Enable checkbox ✓

### 3. Also Add (if using):
- iTerm2: `/Applications/iTerm.app`
- Cursor: `/Applications/Cursor.app`

### 4. Test
```bash
scribe inject-auto
```

Should now work without errors! 🔥

---

## Alternative (No Permissions Needed)

If you don't want to grant Accessibility permissions:

**Use Extension Instead:**
```
Cmd+Shift+S  →  Context copied to clipboard
Cmd+V        →  Paste into Cursor chat
```

Or:
```
Cmd+Shift+P  →  "Scribe: Inject Identity"
```

Both work without any special permissions! ✅

