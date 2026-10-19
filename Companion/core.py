"""Pure launch-protection and allowlist logic; camera and training live in app.py."""
import os
import sys
import shutil
from pathlib import Path
from urllib.parse import urlparse


def normalize(points):
    import numpy as np
    coords = np.asarray(points, dtype=np.float32)
    centered = coords - coords[0]
    scale = float(np.max(np.linalg.norm(centered, axis=1)))
    if scale < 1e-6:
        raise ValueError("Hand landmarks have no measurable scale")
    return (centered / scale).flatten()


class LaunchGate:
    def __init__(self):
        self.active = None
        self.since = 0
        self.last = float("-inf")
        self.latched = False

    def update(self, gesture, confidence, now, threshold, hold, cooldown):
        if gesture is None or confidence < threshold:
            self.active = None
            self.latched = False
            return False
        if self.active != gesture:
            self.active = gesture
            self.since = now
            self.latched = False
            return False
        if not self.latched and now - self.since >= hold and now - self.last >= cooldown:
            self.last = now
            self.latched = True
            return True
        return False


def valid_website(value):
    url = urlparse(value)
    return url.scheme == "https" and bool(url.hostname) and url.username is None and url.password is None


# ── Approved application list ─────────────────────────────────────────────────
# Each entry: display name -> list of candidate paths (first found wins)
# Paths may use env-var-style strings resolved at runtime.

APPROVED_APPS = [
    "VS Code", "Chrome", "Spotify",
    "Edge", "Firefox", "Brave",
    "Notepad", "Notepad++",
    "Calculator", "Paint",
    "File Explorer", "Task Manager",
    "Word", "Excel", "PowerPoint", "Outlook",
    "Teams", "Zoom", "Discord", "Slack", "WhatsApp", "Telegram",
    "Android Studio", "Kiro", "Cursor", "Windsurf",
    "PyCharm", "IntelliJ", "Eclipse",
    "MongoDB Compass", "DBeaver", "Postman",
    "VLC", "OBS", "Steam", "Epic Games",
    "Blender", "GIMP", "Figma",
    "Tableau",
    "YouTube", "Website",
]

# Windows candidate paths per app
_WIN_PATHS: dict[str, list[str]] = {
    "VS Code":        [r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
                       r"%PROGRAMFILES%\Microsoft VS Code\Code.exe"],
    "Chrome":         [r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
                       r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe",
                       r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"],
    "Spotify":        [r"%APPDATA%\Spotify\Spotify.exe",
                       r"%LOCALAPPDATA%\Spotify\Spotify.exe"],
    "Edge":           [r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe",
                       r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"],
    "Firefox":        [r"%PROGRAMFILES%\Mozilla Firefox\firefox.exe",
                       r"%PROGRAMFILES(X86)%\Mozilla Firefox\firefox.exe"],
    "Brave":          [r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"],
    "Notepad":        [r"%SYSTEMROOT%\System32\notepad.exe"],
    "Notepad++":      [r"%PROGRAMFILES%\Notepad++\notepad++.exe",
                       r"%PROGRAMFILES(X86)%\Notepad++\notepad++.exe"],
    "Calculator":     [r"%SYSTEMROOT%\System32\calc.exe"],
    "Paint":          [r"%SYSTEMROOT%\System32\mspaint.exe"],
    "File Explorer":  [r"%SYSTEMROOT%\explorer.exe"],
    "Task Manager":   [r"%SYSTEMROOT%\System32\Taskmgr.exe"],
    "Word":           [r"%PROGRAMFILES%\Microsoft Office\root\Office16\WINWORD.EXE",
                       r"%PROGRAMFILES(X86)%\Microsoft Office\root\Office16\WINWORD.EXE"],
    "Excel":          [r"%PROGRAMFILES%\Microsoft Office\root\Office16\EXCEL.EXE",
                       r"%PROGRAMFILES(X86)%\Microsoft Office\root\Office16\EXCEL.EXE"],
    "PowerPoint":     [r"%PROGRAMFILES%\Microsoft Office\root\Office16\POWERPNT.EXE",
                       r"%PROGRAMFILES(X86)%\Microsoft Office\root\Office16\POWERPNT.EXE"],
    "Outlook":        [r"%PROGRAMFILES%\Microsoft Office\root\Office16\OUTLOOK.EXE",
                       r"%PROGRAMFILES(X86)%\Microsoft Office\root\Office16\OUTLOOK.EXE"],
    "Teams":          [r"%LOCALAPPDATA%\Microsoft\Teams\current\Teams.exe",
                       r"%PROGRAMFILES%\Microsoft\Teams\current\Teams.exe"],
    "Zoom":           [r"%APPDATA%\Zoom\bin\Zoom.exe",
                       r"%PROGRAMFILES%\Zoom\bin\Zoom.exe"],
    "Discord":        [r"%LOCALAPPDATA%\Discord\Update.exe",
                       r"%LOCALAPPDATA%\Discord\app-1.0.9167\Discord.exe"],
    "Slack":          [r"%LOCALAPPDATA%\slack\slack.exe"],
    "WhatsApp":       [r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"],
    "Telegram":       [r"%APPDATA%\Telegram Desktop\Telegram.exe"],
    "Android Studio": [r"%PROGRAMFILES%\Android\Android Studio\bin\studio64.exe",
                       r"D:\setup\android-studio\bin\studio64.exe"],
    "Kiro":           [r"%LOCALAPPDATA%\Programs\kiro\Kiro.exe"],
    "Cursor":         [r"%LOCALAPPDATA%\Programs\cursor\Cursor.exe"],
    "Windsurf":       [r"%LOCALAPPDATA%\Programs\windsurf\Windsurf.exe"],
    "PyCharm":        [r"%LOCALAPPDATA%\Programs\PyCharm\bin\pycharm64.exe",
                       r"%PROGRAMFILES%\JetBrains\PyCharm\bin\pycharm64.exe"],
    "IntelliJ":       [r"%LOCALAPPDATA%\Programs\IntelliJ IDEA\bin\idea64.exe",
                       r"%PROGRAMFILES%\JetBrains\IntelliJ IDEA\bin\idea64.exe"],
    "Eclipse":        [r"D:\setup\eclipse\eclipse.exe",
                       r"C:\eclipse\eclipse.exe"],
    "MongoDB Compass":[r"%LOCALAPPDATA%\MongoDBCompass\MongoDBCompass.exe"],
    "DBeaver":        [r"%PROGRAMFILES%\DBeaver\dbeaver.exe",
                       r"%PROGRAMFILES(X86)%\DBeaver\dbeaver.exe"],
    "Postman":        [r"%LOCALAPPDATA%\Postman\Postman.exe"],
    "VLC":            [r"%PROGRAMFILES%\VideoLAN\VLC\vlc.exe",
                       r"%PROGRAMFILES(X86)%\VideoLAN\VLC\vlc.exe"],
    "OBS":            [r"%PROGRAMFILES%\obs-studio\bin\64bit\obs64.exe"],
    "Steam":          [r"%PROGRAMFILES(X86)%\Steam\Steam.exe",
                       r"%PROGRAMFILES%\Steam\Steam.exe"],
    "Epic Games":     [r"%LOCALAPPDATA%\EpicGamesLauncher\Portal\Binaries\Win64\EpicGamesLauncher.exe"],
    "Blender":        [r"%PROGRAMFILES%\Blender Foundation\Blender 4.0\blender.exe",
                       r"%PROGRAMFILES%\Blender Foundation\Blender\blender.exe"],
    "GIMP":           [r"%PROGRAMFILES%\GIMP 2\bin\gimp-2.10.exe",
                       r"%PROGRAMFILES(X86)%\GIMP 2\bin\gimp-2.10.exe"],
    "Figma":          [r"%LOCALAPPDATA%\Figma\Figma.exe"],
    "Tableau":        [r"%PROGRAMFILES%\Tableau\Tableau 2025.2\bin\tableau.exe",
                       r"%PROGRAMFILES%\Tableau\Tableau 2024.1\bin\tableau.exe"],
}

# macOS app names (for `open -a`)
_MAC_NAMES: dict[str, str] = {
    "VS Code": "Visual Studio Code", "Chrome": "Google Chrome",
    "Spotify": "Spotify", "Edge": "Microsoft Edge", "Firefox": "Firefox",
    "Brave": "Brave Browser", "Notepad": "TextEdit", "Calculator": "Calculator",
    "Word": "Microsoft Word", "Excel": "Microsoft Excel",
    "PowerPoint": "Microsoft PowerPoint", "Outlook": "Microsoft Outlook",
    "Teams": "Microsoft Teams", "Zoom": "zoom.us", "Discord": "Discord",
    "Slack": "Slack", "WhatsApp": "WhatsApp", "Telegram": "Telegram",
    "Android Studio": "Android Studio", "Kiro": "Kiro", "Cursor": "Cursor",
    "Windsurf": "Windsurf", "PyCharm": "PyCharm", "IntelliJ": "IntelliJ IDEA",
    "MongoDB Compass": "MongoDB Compass", "Postman": "Postman",
    "VLC": "VLC", "OBS": "OBS", "Steam": "Steam",
    "Blender": "Blender", "GIMP": "GIMP", "Figma": "Figma",
}

# Linux executable names (checked via shutil.which)
_LINUX_CMDS: dict[str, list[str]] = {
    "VS Code": ["code"], "Chrome": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"],
    "Spotify": ["spotify"], "Edge": ["microsoft-edge", "msedge"],
    "Firefox": ["firefox"], "Brave": ["brave-browser", "brave"],
    "Notepad": ["gedit", "kate", "mousepad", "xed"],
    "Calculator": ["gnome-calculator", "kcalc", "mate-calc"],
    "Word": ["libreoffice", "soffice"], "Excel": ["libreoffice", "soffice"],
    "PowerPoint": ["libreoffice", "soffice"],
    "Teams": ["teams", "microsoft-teams"],
    "Zoom": ["zoom"], "Discord": ["discord"],
    "Slack": ["slack"], "Telegram": ["telegram-desktop", "telegram"],
    "Android Studio": ["studio.sh", "android-studio"],
    "Cursor": ["cursor"], "PyCharm": ["pycharm", "pycharm.sh"],
    "IntelliJ": ["idea", "idea.sh"],
    "MongoDB Compass": ["mongodb-compass"],
    "Postman": ["postman"], "VLC": ["vlc"],
    "OBS": ["obs", "obs-studio"], "Steam": ["steam"],
    "Blender": ["blender"], "GIMP": ["gimp"], "Figma": ["figma-linux"],
}


def _expand(path: str) -> Path:
    """Expand %ENV_VAR% style variables and return a Path."""
    return Path(os.path.expandvars(path))


def approved_executable(app: str) -> Path:
    """Find the executable path for a Windows app. Raises ValueError if not found."""
    candidates = _WIN_PATHS.get(app, [])
    for raw in candidates:
        p = _expand(raw)
        if p.is_file():
            return p
    raise ValueError(f"{app} is not installed in an approved location.")


def approved_command(app: str, platform: str | None = None) -> list[str]:
    """
    Return the command list to launch an approved app on the current platform.
    Raises ValueError if the app is not approved or not installed.
    """
    platform = platform or sys.platform

    if app not in APPROVED_APPS:
        raise ValueError(f"'{app}' is not in the approved application list.")

    # Websites handled by caller
    if app in ("YouTube", "Website"):
        raise ValueError("Website/YouTube launches are handled by the caller.")

    if platform == "win32":
        return [str(approved_executable(app))]

    if platform == "darwin":
        name = _MAC_NAMES.get(app)
        if not name:
            raise ValueError(f"{app} is not supported on macOS.")
        for folder in (Path("/Applications"), Path.home() / "Applications"):
            if (folder / f"{name}.app").is_dir():
                return ["/usr/bin/open", "-a", name]
        raise ValueError(f"{app} ({name}.app) is not installed in /Applications or ~/Applications.")

    if platform.startswith("linux"):
        for cmd in _LINUX_CMDS.get(app, []):
            exe = shutil.which(cmd)
            if exe:
                return [exe]
        raise ValueError(f"{app} is not installed as an approved executable on PATH.")

    raise ValueError("Supported platforms: Windows, macOS, Linux.")
