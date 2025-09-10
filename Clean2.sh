#!/usr/bin/env bash
# auto_run_clean2.sh — download and run your Clean2.py script from GitHub.

# Raw URL of the latest Clean2.py
URL="https://raw.githubusercontent.com/vimalisgoodboy/kali/refs/heads/main/Clean2.py"
SCRIPT="Clean2.py"

echo "⬇ Downloading Clean2.py from GitHub..."
if ! curl -fsSL -o "$SCRIPT" "$URL"; then
    echo "❌ Failed to download Clean2.py. Exiting."
    exit 1
fi

chmod +x "$SCRIPT"

# Check Python3 availability
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python3."
    exit 1
fi

echo "🚀 Running Clean2.py (will wipe all Chrome & Edge data)..."
python3 "$SCRIPT"
echo "✅ Clean2.py has finished execution."
