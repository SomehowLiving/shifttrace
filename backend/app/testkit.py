"""Test feed for trying SHIFTTRACE without a machine (demo_data/testkit.json).

Scenes replace the camera with a recorded panel image or video; lines are recorded questions the browser plays
into the microphone, so the real Agora agent hears and sees them exactly as it would a technician. Which items a
session offers comes from the file's `assets` / `tasks` filters, not from code.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from .packs import PROJECT_DIR

KIT_FILE = Path(os.getenv("SHIFTTRACE_TESTKIT", str(PROJECT_DIR / "demo_data" / "testkit.json")))
MEDIA_DIRS = [PROJECT_DIR / "experiments" / "media" / "generated", PROJECT_DIR / "experiments" / "media" / "web"]
TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webm": "video/webm", ".wav": "audio/wav", ".mp4": "video/mp4"}


@lru_cache(maxsize=1)
def _kit() -> dict[str, Any]:
    if not KIT_FILE.exists():
        return {"scenes": [], "lines": []}
    kit = json.loads(KIT_FILE.read_text(encoding="utf-8"))
    texts: dict[str, str] = {}
    for d in MEDIA_DIRS:
        f = d / "utterances.json"
        if f.exists():
            texts.update(json.loads(f.read_text(encoding="utf-8-sig")))
    for line in kit.get("lines", []):
        key = Path(line["file"]).stem.removeprefix("utt_")
        line.setdefault("text", texts.get(key, key.replace("_", " ")))
    return kit


def reload() -> None:
    _kit.cache_clear()


def _offered(item: dict[str, Any], asset_id: str | None, task_id: str | None) -> bool:
    if asset_id and item.get("assets") and asset_id not in item["assets"]:
        return False
    if task_id and item.get("tasks") and task_id not in item["tasks"]:
        return False
    return True


def for_session(asset_id: str | None, task_id: str | None) -> dict[str, Any]:
    kit = _kit()
    url = lambda f: f"/api/testkit/media/{f}"
    scenes = [{**s, "url": url(s["file"])} for s in kit.get("scenes", []) if _offered(s, asset_id, None) and media_path(s["file"])]
    ids = {s["id"] for s in scenes}
    lines = [{**l, "url": url(l["file"]), "scene": l.get("scene") if l.get("scene") in ids else None}
             for l in kit.get("lines", []) if _offered(l, asset_id, task_id) and media_path(l["file"])]
    return {"scenes": scenes, "lines": lines}


def media_path(name: str) -> Path | None:
    """Only files named in testkit.json are served (no path traversal, no browsing the media folders)."""
    kit = _kit()
    allowed = {x["file"] for x in kit.get("scenes", []) + kit.get("lines", [])}
    if name not in allowed or "/" in name or "\\" in name or Path(name).suffix.lower() not in TYPES:
        return None
    for d in MEDIA_DIRS:
        p = d / name
        if p.is_file():
            return p
    return None
