#!/data/data/com.termux/files/usr/bin/bash
# SUPPERTIME - Termux dependencies installer

echo "🎭 Installing SUPPERTIME dependencies for Termux..."

# Only install what we need for Termux (no Telegram bot)
pip install openai python-dotenv

echo "✅ Done! Run: python suppertime.py"

