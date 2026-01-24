#!/bin/bash

# Automation Advisor - Server Launcher
# Starts the web server with voice-enabled interface

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     AUTOMATION ADVISOR - WEB SERVER LAUNCHER             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check for dependencies
echo "Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ Flask not found. Installing dependencies..."
    pip3 install -r requirements.txt
else
    echo "✅ Dependencies OK"
fi

echo ""
echo "Starting server..."
echo ""

# Set default port if not provided
PORT=${1:-8080}

# Launch server
python3 server.py --mode server --port $PORT

# Or directly launch web server:
# python3 server_web.py --port $PORT
