"""
MongoDB persistence layer for Gustee.

Collections
-----------
gestures        One document per gesture mapping (id, name, symbol, app, target, enabled, samples)
settings        Single document holding confidence/hold/cooldown/camera
training_runs   One document per completed training run (timestamp, accuracy, classes, epochs)
launch_history  One document per app launch attempt (id, gesture, app, time, confidence, success)

The companion falls back to local JSON if MONGO_URI is not set or the connection fails,
so the app works offline too.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# ── Connection ────────────────────────────────────────────────────────────────

_client = None
_db = None
_available = False


def connect(uri: str, db_name: str = "gustee") -> bool:
    """
    Open a MongoDB connection.  Returns True on success, False if unreachable.
    Safe to call multiple times; re-uses the existing client if already connected.
    """
    global _client, _db, _available
    if _available:
        return True
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ConfigurationError
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            tlsAllowInvalidCertificates=False,
            tls=True,
        )
        # Force a round-trip to confirm the server is reachable
        _client.admin.command("ping")
        _db = _client[db_name]
        _ensure_indexes()
        _available = True
        log.info("MongoDB connected: %s / %s", uri.split("@")[-1], db_name)
        return True
    except Exception as exc:
        log.warning("MongoDB unavailable (%s). Using local JSON fallback.", exc)
        _available = False
        return False


def is_available() -> bool:
    return _available


def status() -> dict:
    """Return a dict suitable for the /db/status endpoint."""
    if not _available:
        return {"connected": False, "db": None}
    try:
        info = _client.server_info()  # type: ignore[union-attr]
        return {
            "connected": True,
            "db": _db.name,  # type: ignore[union-attr]
            "version": info.get("version", "unknown"),
        }
    except Exception as exc:
        return {"connected": False, "db": None, "error": str(exc)}


def _ensure_indexes():
    """Create indexes that make common queries fast."""
    _db["gestures"].create_index("id", unique=True)
    _db["launch_history"].create_index([("time", -1)])
    _db["training_runs"].create_index([("finished_at", -1)])


# ── Gestures ──────────────────────────────────────────────────────────────────

def load_gestures() -> list[dict]:
    """Return all gesture documents ordered by id, or [] on failure."""
    if not _available:
        return []
    try:
        return list(_db["gestures"].find({}, {"_id": 0}).sort("id", 1))
    except Exception as exc:
        log.error("load_gestures: %s", exc)
        return []


def save_gesture(mapping: dict):
    """Upsert a single gesture document (matched by id)."""
    if not _available:
        return
    try:
        doc = {k: mapping[k] for k in ("id", "name", "symbol", "app", "target", "enabled", "samples")}
        _db["gestures"].update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
    except Exception as exc:
        log.error("save_gesture: %s", exc)


def save_all_gestures(mappings: list[dict]):
    """Replace the entire gestures collection in one bulk operation."""
    if not _available:
        return
    try:
        from pymongo import ReplaceOne
        ops = [
            ReplaceOne(
                {"id": m["id"]},
                {k: m[k] for k in ("id", "name", "symbol", "app", "target", "enabled", "samples")},
                upsert=True,
            )
            for m in mappings
        ]
        if ops:
            _db["gestures"].bulk_write(ops, ordered=False)
    except Exception as exc:
        log.error("save_all_gestures: %s", exc)


def update_gesture_samples(gesture_id: str, sample_count: int):
    """Update just the sample count for one gesture."""
    if not _available:
        return
    try:
        _db["gestures"].update_one({"id": gesture_id}, {"$set": {"samples": sample_count}})
    except Exception as exc:
        log.error("update_gesture_samples: %s", exc)


# ── Settings ──────────────────────────────────────────────────────────────────

def load_settings() -> Optional[dict]:
    """Return the settings document, or None if not stored yet."""
    if not _available:
        return None
    try:
        doc = _db["settings"].find_one({}, {"_id": 0})
        return doc or None
    except Exception as exc:
        log.error("load_settings: %s", exc)
        return None


def save_settings(settings: dict):
    """Upsert the single settings document."""
    if not _available:
        return
    try:
        _db["settings"].update_one({}, {"$set": settings}, upsert=True)
    except Exception as exc:
        log.error("save_settings: %s", exc)


# ── Training runs ─────────────────────────────────────────────────────────────

def log_training_run(gesture_ids: list[str], accuracy: float, epochs: int, sample_counts: dict[str, int]):
    """
    Insert a training-run record.

    Parameters
    ----------
    gesture_ids   Ordered list of gesture IDs used for this run.
    accuracy      Validation accuracy (0-100).
    epochs        Number of epochs trained.
    sample_counts Mapping of gesture_id -> sample count at training time.
    """
    if not _available:
        return
    try:
        _db["training_runs"].insert_one({
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "gesture_ids": gesture_ids,
            "accuracy": round(accuracy, 2),
            "epochs": epochs,
            "sample_counts": sample_counts,
        })
    except Exception as exc:
        log.error("log_training_run: %s", exc)


def load_training_runs(limit: int = 20) -> list[dict]:
    """Return the most recent training runs, newest first."""
    if not _available:
        return []
    try:
        return list(
            _db["training_runs"]
            .find({}, {"_id": 0})
            .sort("finished_at", -1)
            .limit(limit)
        )
    except Exception as exc:
        log.error("load_training_runs: %s", exc)
        return []


# ── Launch history ────────────────────────────────────────────────────────────

def log_launch(entry: dict):
    """
    Insert a single launch-history document.

    Expected keys: id, gesture, app, time, confidence, success
    """
    if not _available:
        return
    try:
        _db["launch_history"].insert_one({k: entry[k] for k in ("id", "gesture", "app", "time", "confidence", "success")})
    except Exception as exc:
        log.error("log_launch: %s", exc)


def load_launch_history(limit: int = 500) -> list[dict]:
    """Return launch history, newest first, without MongoDB _id."""
    if not _available:
        return []
    try:
        return list(
            _db["launch_history"]
            .find({}, {"_id": 0})
            .sort("time", -1)
            .limit(limit)
        )
    except Exception as exc:
        log.error("load_launch_history: %s", exc)
        return []
