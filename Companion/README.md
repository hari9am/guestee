# Gustee desktop companion

The Gustee companion is a separate desktop app. Install it once and it starts when you sign in; it runs locally in the system tray/menu bar while the computer is awake. Its built-in hand gestures work without pairing or using the website. Open the website only to connect with the one-time pairing key when you want to add or retrain gestures. Samples, mappings, and trained custom models are saved on that computer.

## Windows
Download and run **Gustee-Setup.exe** from the [latest GitHub release](https://github.com/hari9am/guestee/releases/latest). The installer adds Gustee to the Start menu and can optionally start it when you sign in. Allow camera access when asked. Use the tray's **Show pairing key** only when you want to configure or train gestures on the website. The installer includes its runtime and does not need Python, Node.js, or a local web server.

The hosted web workspace is at https://gestuee.netlify.app; the local companion does not start a local web server.

## macOS
Download **Gustee-macOS.zip** from the [latest release](https://github.com/hari9am/guestee/releases/latest), open it, and double-click **install-macos.command**. This installs the app under `~/Applications`, starts it at sign-in, and shows Gustee in the menu bar. On first launch, macOS may ask you to allow the downloaded app; allow camera access in System Settings → Privacy & Security → Camera if prompted.

> The `setup.sh` and `start.sh` scripts in this folder are developer/source-install helpers. End users should use the packaged installer bundle above instead of running shell commands manually.

## Linux
Download **Gustee-Linux-x64.tar.gz** from the [latest release](https://github.com/hari9am/guestee/releases/latest), extract it, and run `./install-linux.sh`. Gustee installs under `~/.local/opt`, starts at sign-in, and runs from the system tray. A desktop session with camera access and a tray/AppIndicator extension may be required. Linux may not show an OS camera permission prompt; Gustee still asks for its own consent. Headless sessions are not supported.

> `setup.sh` is only for bootstrapping a local Python environment from source. For normal use, install the release package and launch the generated app from the OS launcher or autostart entry.

## Consent and background controls
No camera opens until you choose **Allow camera access**. Consent is required anew each time the companion starts. The pretrained gesture recognizer and built-in mappings are included with the app, so they are ready without setup. Custom training adds a local model without removing built-in gestures.

The tray menu includes **Show pairing key**, **Allow camera access**, **Start recognition**, **Pause and release camera**, **Revoke camera access**, and **Quit Gustee**. Pause stops recording as well as recognition and releases the camera. Revoke also removes the companion's in-session consent. The operating-system privacy indicators and camera LED are never hidden. Quit stops the local server and camera worker.

Copy the key from the initial pairing window (or tray → Show pairing key), then paste it in **Connect device** on the website when adding or training gestures. The camera-consent and pairing windows are shown on startup; dismiss them to continue in the background. No continuous camera window is shown. Camera recognition and all training happen locally. The browser offers a live frame only while connected and a session is active. Chrome/Edge may ask for local-network access; this is separate from native camera permission.

## Teach your gestures
To add a custom pose, open the website, pair this computer, record at least 30 samples, and train. The companion saves samples and the learned model locally. Built-in gestures remain available while the custom gesture is added. Use **Start recognition** in the companion tray to run gestures whenever the computer is awake and signed in.

## Privacy, storage, and launching
Camera processing, samples, model, configuration and history stay local:
- Windows: %LOCALAPPDATA%\Gustee
- macOS: ~/Library/Application Support/Gustee
- Linux: $XDG_DATA_HOME/Gustee (default ~/.local/share/Gustee)

Only approved Chrome/Chromium, Spotify and VS Code commands are launched, with shell execution disabled. Windows uses standard install paths; macOS checks /Applications and ~/Applications; Linux checks fixed executable names on PATH. YouTube/Website uses the default browser and HTTPS only. Arbitrary executable paths from the browser are not accepted. A pairing key changes on every restart and is never written to logs.

The service binds only to 127.0.0.1:8765. Browser origins are localhost:8080, localhost:8765, `https://gestuee.netlify.app`, and HTTPS lovable.app. Set GUSTEE_ORIGIN to the exact origin for your custom domain. Do not expose port 8765 outside your computer. If the browser blocks loopback access, use one with local-network permission support.
