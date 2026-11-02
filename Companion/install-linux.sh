#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
APP_DIR="${HOME}/.local/opt/gestuee"
BIN_DIR="${HOME}/.local/bin"
AUTOSTART_DIR="${HOME}/.config/autostart"

mkdir -p "$APP_DIR" "$BIN_DIR" "$AUTOSTART_DIR"
rm -f "$BIN_DIR/gustee" "$HOME/.local/share/applications/gustee.desktop" "$AUTOSTART_DIR/gustee.desktop"
cp -R "$SOURCE_DIR/Gestuee/." "$APP_DIR/"
cp "$SOURCE_DIR/gestuee-icon.png" "$APP_DIR/"
cat > "$BIN_DIR/gestuee" <<EOF
#!/usr/bin/env sh
cd "$APP_DIR"
exec "$APP_DIR/Gestuee"
EOF
chmod +x "$BIN_DIR/gestuee"
cat > "$HOME/.local/share/applications/gestuee.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Gestuee Companion
Comment=Local gesture recognition and launcher
Exec=$BIN_DIR/gestuee
Icon=$APP_DIR/gestuee-icon.png
Terminal=false
Categories=Utility;
EOF
cat > "$AUTOSTART_DIR/gestuee.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Gestuee Companion
Exec=$BIN_DIR/gestuee
Icon=$APP_DIR/gestuee-icon.png
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo 'Gestuee was installed and will start when you sign in.'
echo 'Open https://gestuee.netlify.app only when you want to pair or train gestures.'
"$BIN_DIR/gestuee" >/dev/null 2>&1 &