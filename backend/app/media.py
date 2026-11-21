"""Camera snapshot storage. The console uploads a JPEG frame from the technician's
camera every few seconds while the camera is on; visual observations attach the
most recent frame as evidence."""
from __future__ import annotations

import time
import uuid

from .config import settings

_latest: dict[str, tuple[float, str]] = {}
MAX_BYTES = 600_000


def save_snapshot(session_id: str, data: bytes) -> str:
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("snapshot must be a JPEG")
    if len(data) > MAX_BYTES:
        raise ValueError("snapshot too large")
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    name = f"{session_id}-{int(time.time())}-{uuid.uuid4().hex[:6]}.jpg"
    (settings.media_dir / name).write_bytes(data)
    previous = _latest.get(session_id)
    _latest[session_id] = (time.time(), name)
    # Keep only frames that evidence references; drop the superseded unreferenced one.
    if previous:
        _maybe_delete(previous[1])
    return name


def latest_snapshot(session_id: str | None, max_age_s: float) -> str | None:
    if not session_id or session_id not in _latest:
        return None
    ts, name = _latest[session_id]
    if time.time() - ts > max_age_s:
        return None
    _pinned.add(name)
    return name


_pinned: set[str] = set()


def _maybe_delete(name: str) -> None:
    if name in _pinned:
        return
    try:
        (settings.media_dir / name).unlink(missing_ok=True)
    except OSError:
        pass
