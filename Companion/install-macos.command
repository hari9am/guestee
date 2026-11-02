#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
APP_SOURCE="$SOURCE_DIR/Gestuee.app"
APP_TARGET="$HOME/Applications/Gestuee.app"
AGENT_DIR="$HOME/Library/LaunchAgents"
AGENT_FILE="$AGENT_DIR/com.gestuee.companion.plist"
LEGACY_AGENT_FILE="$AGENT_DIR/com.gustee.companion.plist"

mkdir -p "$HOME/Applications" "$AGENT_DIR"
if [ -f "$LEGACY_AGENT_FILE" ]; then
  if launchctl print "gui/$(id -u)/com.gustee.companion" >/dev/null 2>&1; then
    launchctl bootout "gui/$(id -u)" "$LEGACY_AGENT_FILE"
  fi
  rm -f "$LEGACY_AGENT_FILE"
fi
rm -rf "$APP_TARGET"
cp -R "$APP_SOURCE" "$APP_TARGET"
cat > "$AGENT_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.gestuee.companion</string>
  <key>ProgramArguments</key><array><string>$APP_TARGET/Contents/MacOS/Gestuee</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><false/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/Gestuee.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/Gestuee.log</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)" "$AGENT_FILE" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$AGENT_FILE"
open "$APP_TARGET"
echo 'Gestuee is installed and will start when you sign in.'
echo 'Open https://gestuee.netlify.app only when you want to pair or train gestures.'