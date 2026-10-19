"""
Gustee cursor controller — v2.

KEY DESIGN DECISIONS
--------------------
1. ONE mapping does everything: add a single "cursor_move" action mapping.
   Move + click + scroll + right-click are all detected automatically from
   hand pose — no separate mappings needed or wanted.

2. Actions are EXCLUSIVE per frame: only ONE action fires per frame based
   on the dominant pose. No action mixing.

3. Smooth cursor: weighted moving average + dead-zone to suppress tremor.

4. Edge-triggered clicks: click fires only on the closed→open transition,
   never continuously.

Pose priority (highest wins):
  PINCH_L  → left click    (thumb–index distance < PINCH_CLOSE)
  PINCH_R  → right click   (thumb–middle distance < PINCH_CLOSE)
  FIST     → drag          (all 4 fingers closed)
  PEACE    → scroll        (index + middle up, ring + pinky down)
  POINT    → cursor move   (index up, others down) — DEFAULT fallback
  OPEN     → cursor move   (4+ fingers up)
"""

import sys
import time
import threading
import logging
from typing import Optional
import math

log = logging.getLogger(__name__)

# ── pyautogui ──────────────────────────────────────────────────────────────────
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0
    _HAS_GUI = True
except ImportError:
    _HAS_GUI = False
    log.warning("pyautogui not installed — cursor control disabled.")

try:
    _SW, _SH = pyautogui.size() if _HAS_GUI else (1920, 1080)
except Exception:
    _SW, _SH = 1920, 1080

# ── Volume (Windows) ───────────────────────────────────────────────────────────
_vol = None
if sys.platform == "win32":
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        _spk = AudioUtilities.GetSpeakers()
        _vol = _spk.EndpointVolume if hasattr(_spk, "EndpointVolume") else \
               cast(_spk.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None),
                    POINTER(IAudioEndpointVolume))
    except Exception as e:
        log.warning("pycaw: %s", e)

# ── Landmark indices ───────────────────────────────────────────────────────────
WRIST      = 0
THUMB_MCP  = 2
THUMB_TIP  = 4
INDEX_MCP  = 5
INDEX_PIP  = 6
INDEX_TIP  = 8
MIDDLE_PIP = 10
MIDDLE_TIP = 12
RING_PIP   = 14
RING_TIP   = 16
PINKY_PIP  = 18
PINKY_TIP  = 20

# ── Tuning ─────────────────────────────────────────────────────────────────────
SMOOTH       = 0.20     # lower = smoother but laggier (0.15–0.30 is good range)
DEAD_ZONE    = 3        # pixels — ignore movements smaller than this
MARGIN       = 0.15     # frame edge margin so you can reach all screen corners
PINCH_CLOSE  = 0.052    # normalised distance → pinch closed
PINCH_OPEN   = 0.11     # normalised distance → pinch fully open (re-arm)
SCROLL_SENS  = 50       # pixels of wrist travel per scroll tick

# ── State ──────────────────────────────────────────────────────────────────────
class _S:
    def __init__(self):
        self._lock         = threading.Lock()
        self.sx: Optional[float] = None   # smoothed screen X
        self.sy: Optional[float] = None   # smoothed screen Y
        # click latches — True while pinch is held closed
        self.lc_held       = False
        self.rc_held       = False
        self.dragging      = False
        # scroll
        self.scroll_ref_y: Optional[float] = None
        # volume
        self.vol_ref_y: Optional[float]    = None
        # double-click
        self.last_lc_time  = 0.0
        self.lc_count      = 0
        # cooldowns
        self._cd: dict[str, float] = {}

    def cd(self, key: str, secs: float) -> bool:
        now = time.monotonic()
        with self._lock:
            if now - self._cd.get(key, 0) >= secs:
                self._cd[key] = now
                return True
        return False

    def reset(self):
        with self._lock:
            if self.dragging:
                try: pyautogui.mouseUp()
                except Exception: pass
            self.sx = self.sy = None
            self.lc_held = self.rc_held = self.dragging = False
            self.scroll_ref_y = self.vol_ref_y = None
            self._cd.clear()

_s = _S()

# ── Helpers ────────────────────────────────────────────────────────────────────
def _pts(lm):
    return [(l.x, l.y, l.z) for l in lm]

def _d(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def _up(pts, tip, pip):
    return pts[tip][1] < pts[pip][1]

def _fingers(pts):
    """[thumb, index, middle, ring, pinky] True=extended. Right hand, mirrored cam."""
    return [
        pts[THUMB_TIP][0] < pts[THUMB_MCP][0],
        _up(pts, INDEX_TIP,  INDEX_PIP),
        _up(pts, MIDDLE_TIP, MIDDLE_PIP),
        _up(pts, RING_TIP,   RING_PIP),
        _up(pts, PINKY_TIP,  PINKY_PIP),
    ]

def _screen(nx, ny):
    x = (nx - MARGIN) / (1 - 2 * MARGIN)
    y = (ny - MARGIN) / (1 - 2 * MARGIN)
    return int(max(0.0, min(1.0, x)) * _SW), int(max(0.0, min(1.0, y)) * _SH)

def _move(pts):
    """Smooth-move cursor to index tip. Returns (sx, sy)."""
    tx, ty = _screen(pts[INDEX_TIP][0], pts[INDEX_TIP][1])
    sx = _s.sx
    sy = _s.sy
    if sx is None:
        _s.sx, _s.sy = float(tx), float(ty)
        return tx, ty
    sx = SMOOTH * tx + (1 - SMOOTH) * sx
    sy = SMOOTH * ty + (1 - SMOOTH) * sy
    _s.sx, _s.sy = sx, sy
    ix, iy = int(sx), int(sy)
    try:
        cx, cy = pyautogui.position()
        if abs(cx - ix) > DEAD_ZONE or abs(cy - iy) > DEAD_ZONE:
            pyautogui.moveTo(ix, iy, duration=0)
    except Exception:
        pass
    return ix, iy

# ── Main dispatch ──────────────────────────────────────────────────────────────
def process_frame(action_type: str, landmarks) -> bool:
    """Called every camera frame. action_type is the mapping's action id."""
    if not _HAS_GUI:
        return False

    pts = _pts(landmarks)
    f   = _fingers(pts)
    did = False

    # ──────────────────────────────────────────────────────────────────────────
    # UNIFIED CURSOR CONTROL
    # One mapping handles everything. Priority: pinch > fist > scroll > move.
    # ──────────────────────────────────────────────────────────────────────────
    if action_type == "cursor_move":
        di = _d(pts[THUMB_TIP], pts[INDEX_TIP])   # thumb–index distance
        dm = _d(pts[THUMB_TIP], pts[MIDDLE_TIP])  # thumb–middle distance
        n_up = sum(f)

        # ── Left click (thumb+index pinch) ─────────────────────────────────
        if di < PINCH_CLOSE:
            if not _s.lc_held:
                _s.lc_held = True
                now = time.monotonic()
                if now - _s.last_lc_time < 0.45:
                    _s.lc_count += 1
                else:
                    _s.lc_count = 1
                _s.last_lc_time = now
                try:
                    if _s.lc_count >= 2:
                        pyautogui.doubleClick()
                        _s.lc_count = 0
                    else:
                        pyautogui.click()
                    did = True
                except Exception:
                    pass
            # Keep cursor smooth while pinching
            _move(pts)
            _s.rc_held = False
            _s.scroll_ref_y = None
            return did

        elif di > PINCH_OPEN:
            _s.lc_held = False   # re-arm

        # ── Right click (thumb+middle pinch) ──────────────────────────────
        if dm < PINCH_CLOSE:
            if not _s.rc_held:
                _s.rc_held = True
                try: pyautogui.rightClick(); did = True
                except Exception: pass
            _move(pts)
            _s.scroll_ref_y = None
            return did

        elif dm > PINCH_OPEN:
            _s.rc_held = False

        # ── Drag (all fingers closed = fist) ──────────────────────────────
        if n_up == 0:
            if not _s.dragging:
                try: pyautogui.mouseDown(); _s.dragging = True
                except Exception: pass
            _move(pts)
            _s.scroll_ref_y = None
            return True

        elif _s.dragging:
            try: pyautogui.mouseUp(); _s.dragging = False
            except Exception: pass

        # ── Scroll (index + middle up, ring + pinky down) ─────────────────
        if f[1] and f[2] and not f[3] and not f[4]:
            wy = pts[WRIST][1]
            if _s.scroll_ref_y is None:
                _s.scroll_ref_y = wy
            delta = (wy - _s.scroll_ref_y) * _SH
            if abs(delta) > SCROLL_SENS:
                ticks = int(delta / SCROLL_SENS)
                try: pyautogui.scroll(-ticks); did = True
                except Exception: pass
                _s.scroll_ref_y = wy
            return did or True

        _s.scroll_ref_y = None

        # ── Move cursor (index up or open palm) ────────────────────────────
        if f[1] or n_up >= 4:
            _move(pts)
            return True

    # ──────────────────────────────────────────────────────────────────────────
    # STANDALONE ACTIONS (separate mappings if user wants them explicitly)
    # ──────────────────────────────────────────────────────────────────────────

    elif action_type == "left_click":
        di = _d(pts[THUMB_TIP], pts[INDEX_TIP])
        if di < PINCH_CLOSE and not _s.lc_held:
            _s.lc_held = True
            now = time.monotonic()
            if now - _s.last_lc_time < 0.45:
                _s.lc_count += 1
            else:
                _s.lc_count = 1
            _s.last_lc_time = now
            try:
                if _s.lc_count >= 2:
                    pyautogui.doubleClick(); _s.lc_count = 0
                else:
                    pyautogui.click()
                did = True
            except Exception: pass
        elif di > PINCH_OPEN:
            _s.lc_held = False

    elif action_type == "right_click":
        dm = _d(pts[THUMB_TIP], pts[MIDDLE_TIP])
        if dm < PINCH_CLOSE and not _s.rc_held:
            _s.rc_held = True
            try: pyautogui.rightClick(); did = True
            except Exception: pass
        elif dm > PINCH_OPEN:
            _s.rc_held = False

    elif action_type == "double_click":
        di = _d(pts[THUMB_TIP], pts[INDEX_TIP])
        if di < PINCH_CLOSE * 0.8 and _s.cd("dbl", 0.7):
            try: pyautogui.doubleClick(); did = True
            except Exception: pass

    elif action_type in ("scroll_up", "scroll_down"):
        if f[1] and f[2] and not f[3] and not f[4]:
            wy = pts[WRIST][1]
            if _s.scroll_ref_y is None:
                _s.scroll_ref_y = wy
            delta = (wy - _s.scroll_ref_y) * _SH
            if abs(delta) > SCROLL_SENS:
                try: pyautogui.scroll(-int(delta / SCROLL_SENS)); did = True
                except Exception: pass
                _s.scroll_ref_y = wy
        else:
            _s.scroll_ref_y = None

    elif action_type == "drag":
        n_up = sum(f)
        if n_up == 0:
            if not _s.dragging:
                try: pyautogui.mouseDown(); _s.dragging = True; did = True
                except Exception: pass
        elif _s.dragging:
            try: pyautogui.mouseUp(); _s.dragging = False; did = True
            except Exception: pass

    elif action_type in ("volume_up", "volume_down"):
        if f[0] and f[1] and not f[2] and not f[3]:
            wy = pts[WRIST][1]
            if _s.vol_ref_y is None:
                _s.vol_ref_y = wy
            delta = (_s.vol_ref_y - wy)
            if abs(delta) > 0.035:
                step = 0.04 * (1 if delta > 0 else -1)
                if _vol is not None:
                    try:
                        cur = _vol.GetMasterVolumeLevelScalar()
                        _vol.SetMasterVolumeLevelScalar(max(0.0, min(1.0, cur + step)), None)
                        did = True
                    except Exception: pass
                elif _HAS_GUI:
                    try: pyautogui.press("volumeup" if delta > 0 else "volumedown"); did = True
                    except Exception: pass
                _s.vol_ref_y = wy
        else:
            _s.vol_ref_y = None

    elif action_type == "mute":
        if _s.cd("mute", 1.2):
            if _vol is not None:
                try: _vol.SetMute(not _vol.GetMute(), None); did = True
                except Exception: pass
            elif _HAS_GUI:
                try: pyautogui.press("volumemute"); did = True
                except Exception: pass

    elif action_type == "media_play_pause":
        if f[0] and not f[1] and not f[2] and not f[3] and f[4]:
            if _s.cd("play", 1.0):
                try: pyautogui.press("playpause"); did = True
                except Exception: pass

    elif action_type == "media_next":
        if f[1] and not f[2] and not f[3] and not f[4] and not f[0]:
            if _s.cd("next", 1.0):
                try: pyautogui.press("nexttrack"); did = True
                except Exception: pass

    elif action_type == "media_prev":
        if f[0] and not f[1] and not f[2] and not f[3] and not f[4]:
            if _s.cd("prev", 1.0):
                try: pyautogui.press("prevtrack"); did = True
                except Exception: pass

    elif action_type == "screenshot":
        if f[1] and f[2] and not f[3] and not f[4] and not f[0]:
            if _s.cd("ss", 2.0):
                try: pyautogui.hotkey("win", "shift", "s"); did = True
                except Exception: pass

    elif action_type == "zoom_in":
        di = _d(pts[THUMB_TIP], pts[INDEX_TIP])
        if di > 0.18 and _s.cd("zi", 0.4):
            try: pyautogui.hotkey("ctrl", "+"); did = True
            except Exception: pass

    elif action_type == "zoom_out":
        di = _d(pts[THUMB_TIP], pts[INDEX_TIP])
        if di < PINCH_CLOSE and _s.cd("zo", 0.4):
            try: pyautogui.hotkey("ctrl", "-"); did = True
            except Exception: pass

    return did


# ── Legacy alias ───────────────────────────────────────────────────────────────
def detect_and_execute(action_type: str, landmarks) -> bool:
    return process_frame(action_type, landmarks)


def reset():
    _s.reset()


# ── Exports ────────────────────────────────────────────────────────────────────
CONTROL_ACTIONS = [
    "cursor_move",
    "left_click",
    "right_click",
    "double_click",
    "scroll_up",
    "scroll_down",
    "drag",
    "volume_up",
    "volume_down",
    "mute",
    "media_play_pause",
    "media_next",
    "media_prev",
    "screenshot",
    "zoom_in",
    "zoom_out",
]

CONTROL_ACTION_LABELS = {
    "cursor_move":      "Move cursor + click + scroll (all-in-one)",
    "left_click":       "Left click — pinch index + thumb",
    "right_click":      "Right click — pinch middle + thumb",
    "double_click":     "Double click — fast double pinch",
    "scroll_up":        "Scroll — index + middle up, move wrist",
    "scroll_down":      "Scroll down — index + middle, move down",
    "drag":             "Drag — fist to hold, open hand to release",
    "volume_up":        "Volume up — thumb + index, move hand up",
    "volume_down":      "Volume down — thumb + index, move hand down",
    "mute":             "Mute / unmute",
    "media_play_pause": "Play / pause — shaka (thumb + pinky)",
    "media_next":       "Next track — index only, pointing right",
    "media_prev":       "Previous track — thumb only",
    "screenshot":       "Screenshot — peace sign held 2 seconds",
    "zoom_in":          "Zoom in — spread thumb + index apart",
    "zoom_out":         "Zoom out — pinch thumb + index close",
}
