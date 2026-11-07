#!/bin/bash
# Install, or with --remove uninstall, an hourly launchd job that refreshes
# the sessiondex index. Run it from the installed skill, not a git checkout,
# so that switching branches cannot break the job.
set -euo pipefail

LABEL="com.sessiondex.index"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
SCRIPT="$(cd "$(dirname "$0")" && pwd)/sessiondex.py"
LOG="$HOME/.local/share/sessiondex/index.log"
DOMAIN="gui/$(id -u)"

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true

if [ "${1:-}" = "--remove" ]; then
  if [ -f "$PLIST" ]; then
    trash "$PLIST"
  fi
  echo "Removed $LABEL"
  exit 0
fi

PYTHON="$(command -v python3)"
mkdir -p "$(dirname "$LOG")"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$SCRIPT</string>
    <string>index</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>$(dirname "$PYTHON"):/usr/bin:/bin</string></dict>
  <key>StartInterval</key><integer>3600</integer>
  <key>RunAtLoad</key><true/>
  <key>Nice</key><integer>10</integer>
  <key>LowPriorityIO</key><true/>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
EOF

plutil -lint "$PLIST" >/dev/null
launchctl bootstrap "$DOMAIN" "$PLIST"
echo "Installed $LABEL: hourly, logging to $LOG"
