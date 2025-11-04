# Termux Widget Setup - Field Presence on Home Screen

**Status:** Ready to use
**Date:** 2025-11-04
**Purpose:** Quick access to Field5, Visualizer, and Genesis status

---

## 📱 What You Get

**3 Home Screen Widgets:**
1. **Field Status** - Check if Field5 is running, start/stop/visualize
2. **Field Visualizer** - Launch hybrid visualizer directly
3. **Genesis Status** - Check Arianna/Monday daemons, read latest digests

---

## 🚀 Installation

### 1. Install Termux:Widget

Download from GitHub (same source as your Termux):
- https://github.com/termux/termux-widget/releases
- Install the APK (Termux:Widget v0.13+)

### 2. Widget Scripts Already Created ✅

Shortcuts are in `~/.shortcuts/`:
```
~/.shortcuts/Field Status.sh
~/.shortcuts/Field Visualizer.sh
~/.shortcuts/Genesis Status.sh
```

### 3. Add Widget to Home Screen

1. Long-press on home screen
2. Select "Widgets"
3. Find "Termux:Widget"
4. Drag to home screen
5. Widget will show available shortcuts!

---

## 🎯 What Each Widget Does

### 1️⃣ Field Status Widget

**Tap to check:**
- ✅ Field ACTIVE → Buttons: "📊 Visualize" | "🛑 Stop"
- ⚪ Field Idle → Button: "▶️ Start"

**Shows:**
- Current Field5 PID
- Quick actions via notification buttons

---

### 2️⃣ Field Visualizer Widget

**Tap to launch:**
- Starts `field_visualiser_hybrid2.py`
- Shows cell population graph
- Interactive visualization

**If already running:**
- Button to restart visualizer

---

### 3️⃣ Genesis Status Widget

**Tap to see:**
- ✨ Arianna daemon status
- 💀 Monday daemon status

**Buttons:**
- "📖 Arianna" → Opens latest Arianna digest
- "📖 Monday" → Opens latest Monday digest

---

## 📂 Where Digests Are Saved

Genesis thoughts are now saved to `/sdcard/`:
```
/sdcard/genesis_arianna_latest.txt
/sdcard/genesis_monday_latest.txt
```

**Why sdcard?**
- Easy to open with any text editor
- Accessible from Mac via ADB
- No Termux permissions needed

---

## 🔧 Notification Fix Applied ✅

**Before:**
- Tap notification → Nothing happens
- `--action` command didn't work

**After:**
- Tap notification → Button "📖 Read Full"
- Opens digest in text editor
- Works with any app (Google Docs, QuickEdit, etc.)

**Files updated:**
- `genesis_arianna.py` - Button with termux-open
- `genesis_monday.py` - Button with termux-open

---

## 🎨 Why This is Cool

**Field Presence:**
- Glanceable status on home screen
- One tap to visualize
- Quick start/stop controls

**Genesis Thoughts:**
- Readable notifications
- Full digests always accessible
- No more "tap does nothing" frustration

**Distributed Presence:**
- Phone home screen = Field status
- Mac (via SSH) = Full logs
- Cursor (via sync) = Complete memory

---

## 🧪 Test It

1. **Add widget to home screen** (if you have Termux:Widget)
2. **Tap "Field Status"** → Should show current status
3. **Tap "Genesis Status"** → Should show daemon PIDs
4. **Tap "📖 Read Full" on notification** → Should open digest!

---

## 📊 Field Visualizer on Widget

The **Field Visualizer** widget launches:
```python
field_visualiser_hybrid2.py
```

**Shows:**
- Live cell population graph
- Birth/death rates
- Resonance metrics
- Age distribution

**Why hybrid2?**
- Best visualizer for Termux
- Real-time updates
- Low resource usage

---

## 🔮 Future Ideas

**Could add:**
- Scribe status widget
- Quick webhook trigger
- Resonance query widget
- Field snapshot export

**For now:** 3 widgets cover the essentials! 🎯

---

## 🛠️ Troubleshooting

### Widget shows "No scripts"
```bash
ls -la ~/.shortcuts/
# Should show 3 .sh files with execute permissions
```

If missing:
```bash
cd ~/ariannamethod
git pull  # Get latest .shortcuts scripts
```

### Notification button doesn't work
- Make sure files are in `/sdcard/genesis_*.txt`
- Check with: `ls -la /sdcard/genesis_*.txt`
- Next Genesis cycle will create them

### Visualizer won't start
```bash
# Check if Field5 is initialized
ls ~/ariannamethod/async_field_forever/field5/

# If missing, run bootstrap:
cd ~/ariannamethod/async_field_forever/field5
./bootstrap_field5.sh
```

---

**Status:** ✅ Ready for home screen presence!
**Next:** Install Termux:Widget and add widgets 🎨

---

Signed-off-by: Claude Defender
Re: Widget setup for Field presence
Context: User wants Field visualizer on home screen
