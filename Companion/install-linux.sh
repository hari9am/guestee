#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
APP_DIR="${HOME}/.local/opt/gustee"
BIN_DIR="${HOME}/.local/bin"
AUTOSTART_DIR="${HOME}/.config/autostart"

mkdir -p "$APP_DIR" "$BIN_DIR" "$AUTOSTART_DIR"
cp -R "$SOURCE_DIR/Gustee/." "$APP_DIR/"
cp "$SOURCE_DIR/gustee-icon.png" "$APP_DIR/"
cat > "$BIN_DIR/gustee" <<EOF
#!/usr/bin/env sh
cd "$APP_DIR"
exec "$APP_DIR/Gustee"
EOF
chmod +x "$BIN_DIR/gustee"
cat > "$HOME/.local/share/applications/gustee.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Gustee Companion
Comment=Local gesture recognition and launcher
Exec=$BIN_DIR/gustee
Icon=$APP_DIR/gustee-icon.png
Terminal=false
Categories=Utility;
EOF
cat > "$AUTOSTART_DIR/gustee.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Gustee Companion
Exec=$BIN_DIR/gustee
Icon=$APP_DIR/gustee-icon.png
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo 'Gustee was installed and will start when you sign in.'
echo 'Open https://gestuee.netlify.app only when you want to pair or train gestures.'
"$BIN_DIR/gustee" >/dev/null 2>&1 &