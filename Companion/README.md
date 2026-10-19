# Gustee desktop companion

Runs in the background on Windows, macOS, and Linux after explicit camera consent. This download contains Python source and setup scripts, not signed native installers. Python 3.11 and a supported desktop tray are required. Recognition continues independently of the browser while the computer is awake and logged in. It does not run before login, during sleep, or automatically at boot.

## Windows
Download and run **Gustee-Setup.exe** from the [latest GitHub release](https://github.com/hari9am/guestee/releases/latest). The installer adds Gustee to the Start menu and can optionally start it when you sign in. Open Gustee, copy the pairing key, and connect it to the hosted website. The installer includes its runtime and does not need Node.js or a local web server. If camera access fails, enable Settings → Privacy & security → Camera → Let desktop apps access your camera. Windows may not show a per-app OS permission dialog; Gustee itself always asks for consent.

The source package remains available for macOS and Linux. Windows source setup is also available by extracting the archive and running **start.bat**; that route requires Python 3.9–3.12. The hosted web workspace is at https://gestiee.vercel.app; the local companion does not start a local web server.

## macOS
Install Python 3.11 from python.org (includes Tk). In Terminal, in this folder, run `bash setup.sh`, then `bash start.sh` (or double-click **start.command**). After setup the terminal can be closed. Allow the consent dialog and any macOS camera prompt. macOS may attribute the camera to Python or your terminal rather than Gustee because this is not a signed .app bundle. Check System Settings → Privacy & Security → Camera if access is denied.

## Linux
Install Python 3.11, its venv and Tk packages, and a supported desktop tray/status icon (GNOME may need an AppIndicator or tray extension). Run `bash setup.sh`, then `bash start.sh`. You can close the terminal afterward. Camera device access is controlled by your distribution/session; Linux may not display an OS camera prompt for a native Python process. Gustee's local consent dialog is still required. If no tray icon appears, check logs/companion.log; do not run on a headless machine. Flatpak-only application installs are not supported by this source companion.

## Consent and background controls
No camera opens until you choose **Allow camera access**. Consent is required anew each time the companion starts. A trained saved model starts recognition after Allow. If no model exists, first pair and train it in the web workspace.

The tray menu includes **Show pairing key**, **Allow camera access**, **Start recognition**, **Pause and release camera**, **Revoke camera access**, and **Quit Gustee**. Pause stops recording as well as recognition and releases the camera. Revoke also removes the companion's in-session consent. The operating-system privacy indicators and camera LED are never hidden. Quit stops the local server and camera worker.

Copy the key from the initial pairing window (or tray → Show pairing key), then paste it in **Connect device** in Gustee. Only the initial permission and pairing windows are visible; dismiss them to continue entirely in the background. No continuous camera window is shown. The browser offers an auto-refreshed live frame while a session is active. Chrome/Edge may ask for local-network access; this is separate from native camera permission.

## Teach your gestures
Record at least 30 samples for every gesture, varying angle, distance, and lighting. Include a neutral/rest pose with its mapping disabled. Stop each recording, train the PyTorch model, then start a session. The initial examples are not trained. New classes or additional recordings invalidate the previous model until retraining. Held-out accuracy may overestimate real-world performance when adjacent frames are similar. Dynamic motion models are not included.

## Privacy, storage, and launching
Camera processing, samples, model, configuration and history stay local:
- Windows: %LOCALAPPDATA%\Gustee
- macOS: ~/Library/Application Support/Gustee
- Linux: $XDG_DATA_HOME/Gustee (default ~/.local/share/Gustee)

Only approved Chrome/Chromium, Spotify and VS Code commands are launched, with shell execution disabled. Windows uses standard install paths; macOS checks /Applications and ~/Applications; Linux checks fixed executable names on PATH. YouTube/Website uses the default browser and HTTPS only. Arbitrary executable paths from the browser are not accepted. A pairing key changes on every restart and is never written to logs.

The service binds only to 127.0.0.1:8765. Browser origins are localhost:8080, localhost:8765, `https://gestiee.vercel.app`, and HTTPS lovable.app. Set GUSTEE_ORIGIN to the exact origin for your custom domain. Do not expose port 8765 outside your computer. If the browser blocks loopback access, use one with local-network permission support.
