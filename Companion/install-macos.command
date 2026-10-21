#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
APP_SOURCE="$SOURCE_DIR/Gustee.app"
APP_TARGET="$HOME/Applications/Gustee.app"
AGENT_DIR="$HOME/Library/LaunchAgents"
AGENT_FILE="$AGENT_DIR/com.gustee.companion.plist"

mkdir -p "$HOME/Applications" "$AGENT_DIR"
rm -rf "$APP_TARGET"
cp -R "$APP_SOURCE" "$APP_TARGET"
cat > "$AGENT_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.gustee.companion</string>
  <key>ProgramArguments</key><array><string>$APP_TARGET/Contents/MacOS/Gustee</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><false/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/Gustee.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/Gustee.log</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)" "$AGENT_FILE" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$AGENT_FILE"
open "$APP_TARGET"
echo 'Gustee is installed and will start when you sign in.'
echo 'Open https://gestuee.netlify.app only when you want to pair or train gestures.'