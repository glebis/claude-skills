#!/bin/bash
# YT Transcript — double-click to launch
# Checks requirements, installs flask if needed, starts the web app.

set -e
cd "$(dirname "$0")"

echo ""
echo "  ================================"
echo "    YT Transcript Downloader"
echo "  ================================"
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found."
    echo "Install from https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

PYTHON=$(command -v python3)
echo "  Python: $PYTHON ($(python3 --version 2>&1))"

# Check yt-dlp
YTDLP=""
if command -v yt-dlp &>/dev/null; then
    YTDLP=$(command -v yt-dlp)
elif [ -x "/usr/local/bin/yt-dlp" ]; then
    YTDLP="/usr/local/bin/yt-dlp"
elif [ -x "/opt/homebrew/bin/yt-dlp" ]; then
    YTDLP="/opt/homebrew/bin/yt-dlp"
fi

if [ -z "$YTDLP" ]; then
    echo ""
    echo "  yt-dlp not found. Downloading from GitHub..."
    YTDLP="$HOME/.local/bin/yt-dlp"
    mkdir -p "$(dirname "$YTDLP")"
    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o "$YTDLP"
    chmod 755 "$YTDLP"
    echo "  Installed yt-dlp to $YTDLP"
fi

echo "  yt-dlp:  $YTDLP"

# Ensure yt-dlp is on PATH for child processes
export PATH="$(dirname "$YTDLP"):$PATH"

# Set up virtual environment
VENV_DIR="$(pwd)/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if ! python3 -c "import flask" 2>/dev/null; then
    echo "  Installing dependencies..."
    pip install --quiet -r requirements.txt
fi

echo "  Flask:   OK"
echo ""
echo "  Starting server... (browser will open)"
echo "  Press Ctrl+C to stop."
echo ""

python3 app.py
