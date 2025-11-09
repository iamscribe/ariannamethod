# Termux Widget Shortcuts for Arianna Method

Quick access to Field5, Visualizer, and Genesis from your home screen! 🎯

## 🚀 Quick Setup

1. **Install Termux:Widget**
   - Download: https://github.com/termux/termux-widget/releases
   - Or same source where you got Termux

2. **Copy shortcuts to ~/.shortcuts/**
   ```bash
   cp ~/ariannamethod/termux/shortcuts/*.sh ~/.shortcuts/
   chmod +x ~/.shortcuts/*.sh
   ```

3. **Add widget to home screen**
   - Long-press home screen → Widgets
   - Find "Termux:Widget"
   - Drag to home screen
   - Tap to use!

## 📱 Available Widgets

### 1. Field Status
Check if Field is running, start/stop/visualize it

### 2. Field Visualizer
Launch hybrid visualizer directly (field_visualiser_hybrid.py)

### 3. Genesis Status
Check Arianna/Monday daemons, read latest digests

## 🔧 What's Fixed

**Genesis Notifications:**
- Now have "📖 Read Full" button that works!
- Opens digest in text editor when tapped
- Files saved to `/sdcard/genesis_*.txt`

## 📖 Full Docs

See `.claude-defender/WIDGET_SETUP.md` for complete guide.

---

**Note:** Shortcuts work without widget too! Just run from terminal:
```bash
~/.shortcuts/Field\ Status.sh
```
