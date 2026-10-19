"""Local consent and tray controls. No camera access is performed here."""
import queue
import threading
import tkinter as tk
from tkinter import messagebox


class Desktop:
    def __init__(self, key, start, pause, revoke, status, quit_app):
        self.key = key
        self.start = start
        self.pause = pause
        self.revoke = revoke
        self.status = status
        self.quit_app = quit_app
        self.tasks = queue.Queue()
        self.root = tk.Tk()
        self.root.withdraw()
        self.icon = None
        self.exiting = False

    def enqueue(self, callback):
        self.tasks.put(callback)

    def drain(self):
        while not self.tasks.empty():
            self.tasks.get_nowait()()
        if not self.exiting:
            self.root.after(150, self.drain)

    def _bring_to_front(self, window):
        """Force a window to appear on top of everything."""
        window.lift()
        window.attributes("-topmost", True)
        window.focus_force()
        window.update()
        # Allow moving it after appearing
        window.after(2000, lambda: window.attributes("-topmost", False))

    def show_key(self):
        window = tk.Toplevel(self.root)
        window.title("Gustee · Connect device")
        window.resizable(False, False)

        # Header
        tk.Label(window, text="Gustee is running in the background",
                 font=("Arial", 14, "bold"), padx=25, pady=15, fg="#206030").pack()
        tk.Label(window, text="Copy the pairing key below and paste it into\n"
                 "Connect device in the Gustee web UI.",
                 padx=25, justify="center").pack()

        # Key field — visible (not masked) so user can see it
        key_frame = tk.Frame(window, padx=25, pady=10)
        key_frame.pack()
        entry = tk.Entry(key_frame, width=50, font=("Courier", 10))
        entry.insert(0, self.key)
        entry.config(state="readonly")
        entry.pack(side="left", padx=(0, 8))

        def copy():
            window.clipboard_clear()
            window.clipboard_append(self.key)
            window.update()
            copy_btn.config(text="Copied!")
            window.after(2000, lambda: copy_btn.config(text="Copy key"))

        copy_btn = tk.Button(key_frame, text="Copy key", command=copy,
                             bg="#2d7a3a", fg="white", padx=8)
        copy_btn.pack(side="left")

        tk.Label(window,
                 text="The tray icon is in your taskbar (bottom-right corner).\n"
                      "Click the   ^   arrow to show hidden icons if you can't see it.\n"
                      "Right-click the Gustee icon to access all controls.",
                 padx=25, pady=8, fg="#555555", justify="center").pack()

        btn_frame = tk.Frame(window, pady=10)
        btn_frame.pack()
        tk.Button(btn_frame, text="Open web UI  (http://localhost:8080)",
                  command=lambda: (window.destroy(), __import__("webbrowser").open("http://localhost:8080")),
                  bg="#1a5c28", fg="white", padx=10, pady=4).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Continue in background",
                  command=window.destroy, padx=10, pady=4).pack(side="left", padx=5)

        self._bring_to_front(window)

    def request_permission(self, on_allow):
        window = tk.Toplevel(self.root)
        window.title("Gustee · Camera permission")
        window.resizable(False, False)
        tk.Label(window, text="Allow background camera access?",
                 font=("Arial", 14, "bold"), padx=25, pady=18).pack()
        tk.Label(window, justify="left", wraplength=400, padx=25,
                 text="Gustee will use your camera to recognize gestures even while the "
                      "browser is closed. Processing stays entirely on this device.\n\n"
                      "The camera LED and OS privacy indicators are never hidden.\n\n"
                      "You can pause, revoke, or quit at any time from the tray icon.").pack()

        def allow():
            window.destroy()
            on_allow()

        btn_frame = tk.Frame(window, pady=12)
        btn_frame.pack()
        tk.Button(btn_frame, text="Allow camera access",
                  command=allow, bg="#2d7a3a", fg="white",
                  padx=14, pady=6, font=("Arial", 11)).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Not now",
                  command=window.destroy, padx=14, pady=6).pack(side="left", padx=8)

        self._bring_to_front(window)

    def resume(self):
        try:
            self.start()
        except Exception as exc:
            messagebox.showerror("Gustee", str(exc), parent=self.root)

    def quit(self):
        self.exiting = True
        self.quit_app()
        if self.icon:
            self.icon.stop()
        self.root.quit()

    def run(self, allow):
        import pystray
        from PIL import Image, ImageDraw, ImageFont

        # Draw a clean "G" icon with brand colors
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle — dark
        draw.ellipse((2, 2, size - 2, size - 2), fill=(20, 23, 24))
        # Outer ring — brand green
        draw.ellipse((2, 2, size - 2, size - 2), outline=(140, 220, 80), width=4)
        # "G" letter in the center
        draw.text((18, 12), "G", fill=(140, 220, 80), font=ImageFont.load_default())
        # Inner dot
        draw.ellipse((28, 28, 36, 36), fill=(140, 220, 80))

        def item(label, callback):
            return pystray.MenuItem(
                label, lambda icon, entry: self.enqueue(callback)
            )

        menu = pystray.Menu(
            pystray.MenuItem("Gustee — gesture launcher", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda _: "● Camera active" if self.status()["camera"] else "○ Camera idle",
                None, enabled=False
            ),
            pystray.Menu.SEPARATOR,
            item("Show pairing key", self.show_key),
            item("Allow camera access", lambda: self.request_permission(allow)),
            item("Start recognition", self.resume),
            item("Pause and release camera", self.pause),
            pystray.Menu.SEPARATOR,
            item("Revoke camera access", self.revoke),
            item("Quit Gustee", self.quit),
        )

        self.icon = pystray.Icon(
            "Gustee", img,
            "Gustee — right-click for controls",
            menu
        )

        try:
            self.icon.run_detached()
        except Exception as exc:
            messagebox.showerror(
                "Gustee",
                f"Could not create system tray icon.\n\n{exc}\n\n"
                "On Windows 11: make sure taskbar settings allow app icons in the system tray.",
                parent=self.root
            )
            self.quit_app()
            return

        # Show pairing key window on startup
        self.show_key()
        # Then ask for camera permission
        self.request_permission(allow)

        self.root.after(150, self.drain)
        self.root.mainloop()
