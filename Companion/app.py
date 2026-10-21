import hmac
import json
import os
import sys
import re
import secrets
import subprocess
import threading
import time
import uuid
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlretrieve

import cv2
import mediapipe as mp
import numpy as np
import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from torch import nn
import uvicorn
from core import LaunchGate, approved_command, normalize, valid_website
import db
import control
from control import CONTROL_ACTIONS

# ── Data directory (local files: samples .npy, model.pt, hand_landmarker.task) ─
DATA = (
    Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Gustee"
    if sys.platform == "win32"
    else Path.home() / "Library/Application Support/Gustee"
    if sys.platform == "darwin"
    else Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "Gustee"
)
DATA.mkdir(parents=True, exist_ok=True)

KEY = secrets.token_urlsafe(32)
lock = threading.RLock()
allowed_origin = os.environ.get("GUSTEE_ORIGIN", "")
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8765",
    "https://gestuee.netlify.app",
]
if allowed_origin:
    origins.append(allowed_origin)

app = FastAPI(docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://[a-zA-Z0-9.-]+\.netlify\.app",
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Pydantic models ────────────────────────────────────────────────────────────

class Mapping(BaseModel):
    id: str = Field(pattern=r"^G\d{2,6}$")
    name: str = Field(min_length=1, max_length=40)
    symbol: str = Field(max_length=12)
    type: str = Field(default="launch")   # "launch" | "action"
    app: str = Field(default="")          # used when type="launch"
    target: str = ""                       # used when type="launch" + website
    action: str = Field(default="")       # used when type="action"
    builtin: str = Field(default="")
    enabled: bool = True
    samples: int = Field(default=0, ge=0)

class Settings(BaseModel):
    confidence: float = Field(default=90, ge=60, le=99)
    hold: float = Field(default=1.5, ge=0.5, le=4)
    cooldown: float = Field(default=5, ge=2, le=15)
    camera: int = Field(default=0, ge=0, le=3)

class GestureId(BaseModel):
    id: str

# ── In-memory state ────────────────────────────────────────────────────────────

default_mappings = [
    dict(id="G01", name="Peace sign",  symbol="✌️", type="launch", app="YouTube", target="https://www.youtube.com", action="", builtin="Victory", enabled=True, samples=0),
    dict(id="G02", name="Closed fist", symbol="✊", type="launch", app="VS Code",  target="",                       action="", builtin="Closed_Fist", enabled=True, samples=0),
    dict(id="G03", name="Thumbs up",   symbol="👍", type="launch", app="Spotify",  target="",                       action="", builtin="Thumb_Up", enabled=True, samples=0),
    dict(id="G04", name="Pointing up", symbol="☝️", type="launch", app="Chrome",  target="",                       action="", builtin="Pointing_Up", enabled=True, samples=0),
]

state = dict(
    listening=False, camera=False, camera_permission=False,
    gesture=None, confidence=0, model=True, accuracy=None,
    mappings=default_mappings, history=[], settings=Settings().model_dump(),
    recording=None, training=False, previewing=False, error=None,
)

shutdown      = threading.Event()
server        = None
samples: dict = {}      # gesture_id -> list of 63-float numpy arrays (in-memory only)
classifier    = None
classes: list = []
frame_jpeg    = None
worker_running = False

# ── Persistence helpers ────────────────────────────────────────────────────────

def _json_fallback_path() -> Path:
    return DATA / "config.json"

def persist():
    """
    Write current state to MongoDB (if connected) AND local JSON (always).
    Local JSON is the offline fallback so the companion still works without internet.
    """
    # 1. Local JSON fallback (atomic write)
    config = {k: state[k] for k in ["mappings", "settings", "history"]}
    temp = DATA / "config.tmp"
    temp.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    temp.replace(_json_fallback_path())

    # 2. MongoDB (non-blocking best-effort)
    if db.is_available():
        db.save_all_gestures(state["mappings"])
        db.save_settings(state["settings"])


def restore():
    """
    Load saved state, preferring MongoDB over local JSON.
    Samples (.npy files) are always read from disk.
    Launch history is loaded from MongoDB if available, otherwise from local JSON.
    """
    global classifier, classes
    try:
        # ── Load gestures & settings ──────────────────────────────────────────
        db_gestures  = db.load_gestures()
        db_settings  = db.load_settings()
        db_history   = db.load_launch_history(500)

        if db_gestures:
            state["mappings"] = [Mapping(**m).model_dump() for m in db_gestures]
        elif _json_fallback_path().exists():
            config = json.loads(_json_fallback_path().read_text(encoding="utf-8"))
            state["mappings"] = [Mapping(**m).model_dump() for m in config["mappings"]]

        builtin_by_id = {mapping["id"]: mapping["builtin"] for mapping in default_mappings}
        for mapping in state["mappings"]:
            if not mapping["builtin"]:
                mapping["builtin"] = builtin_by_id.get(mapping["id"], "")

        if db_settings:
            state["settings"] = Settings(**db_settings).model_dump()
        elif _json_fallback_path().exists():
            config = json.loads(_json_fallback_path().read_text(encoding="utf-8"))
            state["settings"] = Settings(**config["settings"]).model_dump()

        if db_history:
            state["history"] = db_history
        elif _json_fallback_path().exists():
            config = json.loads(_json_fallback_path().read_text(encoding="utf-8"))
            state["history"] = config.get("history", [])[:500]

        # ── Load sample arrays from disk ──────────────────────────────────────
        for m in state["mappings"]:
            path = DATA / f"{m['id']}.npy"
            samples[m["id"]] = list(np.load(path, allow_pickle=False)) if path.exists() else []
            m["samples"] = len(samples[m["id"]])
            # Keep MongoDB sample count in sync with what's on disk
            if db.is_available():
                db.update_gesture_samples(m["id"], m["samples"])

        # ── Load PyTorch model ────────────────────────────────────────────────
        if (DATA / "model.pt").exists():
            saved = torch.load(DATA / "model.pt", map_location="cpu", weights_only=True)
            trained_ids = [m["id"] for m in state["mappings"] if len(samples.get(m["id"], [])) >= 30]
            if saved["classes"] == trained_ids:
                classes = saved["classes"]
                classifier = network(len(classes))
                classifier.load_state_dict(saved["weights"])
                classifier.eval()
                state.update(model=True, accuracy=saved["accuracy"])

    except Exception as exc:
        state["error"] = f"Saved workspace could not be loaded: {exc}"

# ── ML helpers ─────────────────────────────────────────────────────────────────

def network(n):
    return nn.Sequential(
        nn.Linear(63, 128), nn.ReLU(), nn.Dropout(0.15),
        nn.Linear(128, 64), nn.ReLU(),
        nn.Linear(64, n),
    )

def invalidate():
    global classifier
    classifier = None
    state.update(model=True, accuracy=None, listening=False)
    (DATA / "model.pt").unlink(missing_ok=True)

# ── Auth middleware ────────────────────────────────────────────────────────────

@app.middleware("http")
async def auth(request: Request, call_next):
    origin = request.headers.get("origin")
    valid_origin = (
        origin is None
        or origin in origins
        or bool(re.fullmatch(r"https://[a-zA-Z0-9.-]+\.netlify\.app", origin))
    )
    if not valid_origin:
        return Response("Origin not allowed", status_code=403)
    if request.method == "OPTIONS":
        response = await call_next(request)
        if request.headers.get("access-control-request-private-network") == "true":
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response
    if not hmac.compare_digest(request.headers.get("authorization", ""), f"Bearer {KEY}"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            {"detail": "Invalid pairing key. Copy the current key from Show pairing key in your companion tray menu."},
            status_code=401,
        )
    return await call_next(request)

# ── REST endpoints ─────────────────────────────────────────────────────────────

@app.get("/status")
def get_status():
    with lock:
        return json.loads(json.dumps(state))

@app.get("/frame")
def get_frame():
    with lock:
        if frame_jpeg is None:
            raise HTTPException(409, "No camera frame yet")
        return Response(frame_jpeg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})

@app.get("/db/status")
def get_db_status():
    return db.status()

@app.get("/training/runs")
def get_training_runs():
    return {"runs": db.load_training_runs(20)}

@app.get("/controls")
def get_controls():
    """Return available cursor/keyboard control actions."""
    return {
        "actions": [
            {"id": k, "label": control.CONTROL_ACTION_LABELS[k]}
            for k in control.CONTROL_ACTIONS
        ]
    }

def ensure_camera():
    """Must be called while holding `lock`."""
    global worker_running
    if not state["camera_permission"]:
        raise HTTPException(403, "Camera access is not allowed. Choose Allow camera access in the Gustee tray menu.")
    if not worker_running:
        worker_running = True
        threading.Thread(target=camera_loop, daemon=True).start()

def _start_recognition():
    """Internal: start gesture session. Raises ValueError on logical errors."""
    with lock:
        if not state["camera_permission"]:
            raise ValueError("Allow camera access from the Gustee tray menu first.")
        if not state["model"]:
            raise ValueError("No gesture recognizer is available. Reinstall Gustee to restore the built-in gesture model.")
        if state["recording"] or state["training"]:
            raise ValueError("Finish recording or training first.")
        state.update(listening=True, error=None)
        ensure_camera()

@app.post("/start")
def start():
    with lock:
        if not state["camera_permission"]:
            raise HTTPException(403, "Allow camera access from the Gustee tray menu first.")
        if not state["model"]:
            raise HTTPException(409, "No gesture recognizer is available. Reinstall Gustee to restore the built-in gesture model.")
        if state["recording"] or state["training"]:
            raise HTTPException(409, "Finish recording or training first.")
        state.update(listening=True, error=None)
        ensure_camera()
    return {"ok": True}

@app.post("/stop")
def stop():
    with lock:
        state.update(listening=False, previewing=False, recording=None, gesture=None, confidence=0)
    control.reset()
    return {"ok": True}

@app.post("/preview")
def preview():
    """Start camera in preview mode without requiring a trained model."""
    with lock:
        if not state["camera_permission"]:
            raise HTTPException(403, "Allow camera access from the Gustee tray menu first.")
        if state["training"]:
            raise HTTPException(409, "Finish training first.")
        state.update(previewing=True, error=None)
        ensure_camera()
    return {"ok": True}

@app.post("/mapping")
def save_mapping(mapping: Mapping):
    with lock:
        if state["training"] or state["recording"] or state["listening"]:
            raise HTTPException(409, "Pause your session and finish recording or training before editing mappings.")
        if mapping.type not in ("launch", "action"):
            raise HTTPException(400, "Mapping type must be 'launch' or 'action'.")
        if mapping.type == "launch":
            if mapping.app not in [
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
                "Blender", "GIMP", "Figma", "Tableau",
                "YouTube", "Website",
            ]:
                raise HTTPException(400, "Application is not approved.")
            if mapping.app in ["YouTube", "Website"] and not valid_website(mapping.target):
                raise HTTPException(400, "Enter a valid HTTPS website address.")
        elif mapping.type == "action":
            if mapping.action not in CONTROL_ACTIONS:
                raise HTTPException(400, f"Unknown action '{mapping.action}'.")
        if any(m["id"] != mapping.id and m["name"].casefold() == mapping.name.strip().casefold() for m in state["mappings"]):
            raise HTTPException(400, "Gesture names must be unique.")
        old = next((m for m in state["mappings"] if m["id"] == mapping.id), None)
        entry = mapping.model_dump()
        entry["samples"] = len(samples.get(mapping.id, []))
        if old:
            if not entry["builtin"]:
                entry["builtin"] = old.get("builtin", "")
            old.update(entry)
        else:
            state["mappings"].append(entry)
            samples[mapping.id] = []
            invalidate()
        # Persist to MongoDB + local JSON
        db.save_gesture(entry)
        persist()
    return {"ok": True}

@app.post("/settings")
def save_settings(settings: Settings):
    with lock:
        if state["camera"] or worker_running:
            raise HTTPException(409, "Stop recording and pause the session before changing camera settings.")
        state["settings"] = settings.model_dump()
        db.save_settings(state["settings"])
        persist()
    return {"ok": True}

@app.post("/record")
def record(data: GestureId):
    with lock:
        if not state["camera_permission"]:
            raise HTTPException(403, "Allow camera access from the Gustee tray menu before recording.")
        if not any(m["id"] == data.id for m in state["mappings"]):
            raise HTTPException(404, "Gesture not found")
        if state["training"] or state["recording"]:
            raise HTTPException(409, "Finish the current recording or training first.")
        invalidate()
        state.update(recording=data.id, error=None)
        ensure_camera()
    return {"ok": True}

@app.post("/record/stop")
def stop_record():
    with lock:
        gid = state["recording"]
        state["recording"] = None
        # Sync updated sample count to MongoDB
        if gid:
            count = len(samples.get(gid, []))
            for m in state["mappings"]:
                if m["id"] == gid:
                    m["samples"] = count
            db.update_gesture_samples(gid, count)
        persist()
    return {"ok": True}

@app.post("/mapping/delete")
def delete_mapping(data: GestureId):
    """Delete a gesture mapping and all its training samples."""
    with lock:
        if state["training"] or state["recording"] or state["listening"]:
            raise HTTPException(409, "Pause your session and finish recording before deleting a gesture.")
        if not any(m["id"] == data.id for m in state["mappings"]):
            raise HTTPException(404, "Gesture not found.")
        # Remove from state
        state["mappings"] = [m for m in state["mappings"] if m["id"] != data.id]
        # Delete training samples from memory and disk
        samples.pop(data.id, None)
        npy = DATA / f"{data.id}.npy"
        npy.unlink(missing_ok=True)
        # Delete from MongoDB
        if db.is_available():
            try:
                db._db["gestures"].delete_one({"id": data.id})
            except Exception:
                pass
        # Invalidate model since class list changed
        invalidate()
        persist()
    return {"ok": True}

@app.post("/samples/delete")
def delete_samples(data: GestureId):
    """Delete only the training samples for a gesture (keep the mapping)."""
    with lock:
        if state["training"] or state["recording"]:
            raise HTTPException(409, "Finish recording or training before clearing samples.")
        if not any(m["id"] == data.id for m in state["mappings"]):
            raise HTTPException(404, "Gesture not found.")
        # Clear samples from memory and disk
        samples[data.id] = []
        npy = DATA / f"{data.id}.npy"
        npy.unlink(missing_ok=True)
        # Reset sample count on the mapping
        for m in state["mappings"]:
            if m["id"] == data.id:
                m["samples"] = 0
        db.update_gesture_samples(data.id, 0)
        # Invalidate model
        invalidate()
        persist()
    return {"ok": True}

@app.post("/train")
def train():
    with lock:
        if state["recording"] or state["training"] or state["listening"]:
            raise HTTPException(409, "Stop your session and recording before training.")
        enabled = [m for m in state["mappings"] if m.get("enabled", True)]
        ready   = [m for m in enabled if len(samples.get(m["id"], [])) >= 30]
        if len(enabled) < 1:
            raise HTTPException(400, "Add at least one enabled gesture before training.")
        if len(ready) < 1:
            raise HTTPException(400, "Record at least 30 samples for at least one gesture before training.")
        # For single-gesture training, we train a binary yes/no model.
        # For multi-gesture, all enabled gestures with 30+ samples are used.
        trainable = ready
        state.update(training=True, error=None)
        state.update(training=True, error=None)
        threading.Thread(target=train_worker, daemon=True).start()
    return {"ok": True}

def train_worker():
    global classifier, classes
    epochs = 250
    try:
        with lock:
            # Only train on gestures that have 30+ samples
            trainable = [m for m in state["mappings"] if len(samples.get(m["id"], [])) >= 30]
            if not trainable:
                state["error"] = "No gestures have enough samples (30+). Record more samples first."
                return
            ids = [m["id"] for m in trainable]
            arrays = [np.stack(samples[i]).copy() for i in ids]
            sample_counts = {i: len(samples[i]) for i in ids}
        rng = np.random.default_rng(42)
        train_x, val_x, train_y, val_y = [], [], [], []
        for index, arr in enumerate(arrays):
            arr = arr[rng.permutation(len(arr))]
            n = max(1, int(len(arr) * 0.2))
            val_x.extend(arr[:n]);  val_y.extend([index] * n)
            train_x.extend(arr[n:]); train_y.extend([index] * (len(arr) - n))
        x  = torch.tensor(np.asarray(train_x), dtype=torch.float32)
        y  = torch.tensor(train_y, dtype=torch.long)
        vx = torch.tensor(np.asarray(val_x),   dtype=torch.float32)
        vy = torch.tensor(val_y,                dtype=torch.long)
        model = network(len(ids))
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        for _ in range(epochs):
            model.train()
            optimizer.zero_grad()
            nn.functional.cross_entropy(model(x), y).backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            accuracy = float((model(vx).argmax(1) == vy).float().mean().item() * 100)
        with lock:
            torch.save({"weights": model.state_dict(), "classes": ids, "accuracy": accuracy}, DATA / "model.pt")
            classifier, classes = model, ids
            state.update(model=True, accuracy=accuracy)
        # Log completed run to MongoDB
        db.log_training_run(ids, accuracy, epochs, sample_counts)
    except Exception as exc:
        with lock:
            state["error"] = f"Training failed: {exc}"
    finally:
        with lock:
            state["training"] = False

# ── Camera loop ────────────────────────────────────────────────────────────────

CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17),
]

def launch(mapping, confidence):
    success = False
    try:
        if mapping["app"] in ["Website", "YouTube"]:
            if not valid_website(mapping["target"]):
                raise ValueError("Only HTTPS websites are approved")
            success = webbrowser.open(mapping["target"])
            if not success:
                raise ValueError("The default browser could not open this website")
        else:
            subprocess.Popen(approved_command(mapping["app"]), shell=False)
            success = True
    except Exception as exc:
        state["error"] = str(exc)

    entry = dict(
        id=str(uuid.uuid4()),
        gesture=mapping["name"],
        app=mapping["app"],
        time=datetime.now(timezone.utc).isoformat(),
        confidence=confidence,
        success=success,
    )
    state["history"].insert(0, entry)
    state["history"] = state["history"][:500]
    # Write to MongoDB + local JSON
    db.log_launch(entry)
    persist()

def camera_loop():
    global worker_running, frame_jpeg
    capture = None
    try:
        model_path = DATA / "gesture_recognizer.task"
        if not model_path.exists():
            bundled_model = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "gesture_recognizer.task"
            if bundled_model.exists():
                import shutil
                shutil.copy2(bundled_model, model_path)
            else:
                urlretrieve(
                    "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task",
                    model_path,
                )
        options = mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
        )
        with lock:
            if not state["camera_permission"] or shutdown.is_set():
                return
            backend = (
                cv2.CAP_DSHOW       if sys.platform == "win32"
                else cv2.CAP_AVFOUNDATION if sys.platform == "darwin"
                else cv2.CAP_V4L2
            )
            capture = cv2.VideoCapture(state["settings"]["camera"], backend)
        if not capture.isOpened():
            raise RuntimeError(
                "Camera unavailable or OS permission denied. Enable camera access in your OS "
                "privacy settings, close other camera apps, or select a different camera."
            )
        gate = LaunchGate()
        last_sample = 0.0
        epoch = time.monotonic()
        with mp.tasks.vision.GestureRecognizer.create_from_options(options) as tracker:
            state["camera"] = True
            while (
                not shutdown.is_set()
                and state["camera_permission"]
                and (state["listening"] or state["recording"] or state["previewing"])
            ):
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Could not read your camera")
                frame = cv2.flip(frame, 1)
                now = time.monotonic()
                result = tracker.recognize_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)),
                    int((now - epoch) * 1000),
                )
                with lock:
                    if shutdown.is_set() or not state["camera_permission"] or not (state["listening"] or state["recording"] or state["previewing"]):
                        break
                    if result.hand_landmarks:
                        points = result.hand_landmarks[0]
                        values = normalize([[p.x, p.y, p.z] for p in points])
                        h, w = frame.shape[:2]
                        for a, b in CONNECTIONS:
                            cv2.line(frame, (int(points[a].x*w), int(points[a].y*h)),
                                     (int(points[b].x*w), int(points[b].y*h)), (140, 245, 200), 2)
                        for p in points:
                            cv2.circle(frame, (int(p.x*w), int(p.y*h)), 4, (140, 245, 200), -1)
                        if state["recording"] and now - last_sample >= 0.2:
                            gid = state["recording"]
                            if len(samples[gid]) >= 3000:
                                state.update(recording=None, error="Sample limit reached (3,000). Train your model to continue.")
                            else:
                                samples[gid].append(values)
                                np.save(DATA / f"{gid}.npy", np.stack(samples[gid]))
                                for m in state["mappings"]:
                                    if m["id"] == gid:
                                        m["samples"] = len(samples[gid])
                            last_sample = now

                        if state["listening"]:
                            # ── Step 1: Run ALL action mappings directly on raw landmarks ──
                            # No ML classifier needed — pure geometry, zero latency
                            for m in state["mappings"]:
                                if m.get("type") == "action" and m.get("enabled") and m.get("action") in CONTROL_ACTIONS:
                                    control.process_frame(m["action"], result.hand_landmarks[0])

                            # ── Step 2: ML classifier for launch mappings only ──
                            recognized = None
                            if result.gestures and result.gestures[0]:
                                category = result.gestures[0][0]
                                if category.category_name not in ("None", "Unknown"):
                                    recognized = (category.category_name, float(category.score), "builtin")
                            if classifier is not None:
                                with torch.no_grad():
                                    probs = torch.softmax(
                                        classifier(torch.from_numpy(values).unsqueeze(0)), dim=1
                                    )[0]
                                learned_confidence = float(probs.max().item())
                                if learned_confidence >= state["settings"]["confidence"] / 100:
                                    recognized = (classes[int(probs.argmax().item())], learned_confidence, "learned")

                            mapping = None
                            if recognized:
                                gesture_id, conf, source = recognized
                                if source == "learned":
                                    mapping = next((m for m in state["mappings"] if m["id"] == gesture_id), None)
                                else:
                                    mapping = next((m for m in state["mappings"] if m.get("builtin") == gesture_id), None)
                            if mapping and mapping.get("type", "launch") == "launch":
                                state.update(gesture=mapping["name"], confidence=conf)
                                s = state["settings"]
                                if gate.update(mapping["id"] if mapping["enabled"] else None, conf, now,
                                               s["confidence"] / 100, s["hold"], s["cooldown"]):
                                    launch(mapping, conf)
                            else:
                                state.update(gesture=None, confidence=0)
                    else:
                        state.update(gesture=None, confidence=0)
                        gate.update(None, 0, now, 0.9, 1, 5)
                        # Release drag if hand disappears
                        control.reset()
                    encoded, image = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    if encoded:
                        frame_jpeg = image.tobytes()
                time.sleep(0.01)
    except Exception as exc:
        with lock:
            state.update(error=str(exc), listening=False, recording=None)
    finally:
        if capture is not None:
            capture.release()
        with lock:
            state.update(camera=False, gesture=None, confidence=0)
            frame_jpeg = None
            worker_running = False
            persist()

# ── Tray callbacks ─────────────────────────────────────────────────────────────

def allow_camera():
    with lock:
        state.update(camera_permission=True, error=None)
        if state["model"] and not state["training"] and not state["recording"]:
            try:
                _start_recognition()
            except Exception as exc:
                state["error"] = str(exc)

def pause_session():
    with lock:
        state.update(listening=False, previewing=False, recording=None, gesture=None, confidence=0)
    control.reset()

def revoke_camera():
    with lock:
        state.update(camera_permission=False, listening=False, previewing=False, recording=None, gesture=None, confidence=0)

def quit_companion():
    shutdown.set()
    revoke_camera()
    if server:
        server.should_exit = True

# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    global server
    from desktop import Desktop

    # ── Load .env file if present (avoids shell %/& escaping issues) ──────────
    app_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    env_path = app_dir / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

    # Connect to MongoDB
    mongo_uri = os.environ.get(
        "MONGO_URI",
        "mongodb+srv://farmconnect:Cham8497%40@findit.qejydei.mongodb.net/gustee?retryWrites=true&w=majority",
    )
    db.connect(mongo_uri, db_name="gustee")

    torch.set_num_threads(2)
    restore()

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8765,
            log_level="warning",
            log_config=None,
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("Companion could not start. Another instance may already be running on port 8765.")

    desktop = Desktop(KEY, _start_recognition, pause_session, revoke_camera, get_status, quit_companion)
    try:
        desktop.run(allow_camera)
    finally:
        quit_companion()
        deadline = time.monotonic() + 5
        while worker_running and time.monotonic() < deadline:
            time.sleep(0.05)
        thread.join(timeout=3)

if __name__ == "__main__":
    main()
