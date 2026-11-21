"""Deterministic visual-evidence capture.

Live runs (19-20 Nov) showed the agent often *says* "I'll record this observation" after describing the
camera view but does not call record_observation, so the evidence timeline missed what was seen. This module
records the agent's spoken description of the camera view as a `camera_model` observation when:
  * the technician's latest final utterance was about the camera / panel / what is visible, and
  * the agent's reply describes the view (or says it cannot see it), and
  * the agent did not record a visual observation itself in this turn.
The item stays labelled as a model observation (unverified) and notes that it was captured from speech.
"""
from __future__ import annotations

import asyncio
import os
import re

from . import media, services as svc
from .bus import bus
from .db import connect, parse_ts, tx, utcnow

CAMERA_Q = re.compile(r"\b(see|seeing|look(ing)? at|panel|display|camera|screen|lamp|light|showing|reading|read me|alarm code|gauge|equipment|machine look)\b", re.I)
VISUAL_A = re.compile(r"(\b(i see|i can see|shows|showing|displays|displayed|reads|reading|lamp|lit|looking at|appears|blurry|too dark|"
                      r"can't see|cannot see|unable to see|not able to see|don't see|do not see|black screen|current view|this is an?|this appears|"
                      r"not clear|unclear|not capturing|not visible|blank|looks like|it seems|seems to be|you are viewing|you're viewing|viewing|"
                      r"you are seeing|you're seeing|in view|visible|pictured)\b|°c|mm/s)", re.I)
DELAY_S = float(os.getenv("CAPTURE_DELAY_S", "3.5"))
_scheduled: set[tuple[str, str]] = set()


def forget(session_id: str | None = None) -> None:
    """Session IDs restart at S-1001 after a data reset, so per-session dedupe keys must be dropped when a
    session ID is (re)issued; otherwise a reused ID silently skips capture (observed in the 21 Nov run)."""
    for key in [k for k in _scheduled if session_id is None or k[0] == session_id]:
        _scheduled.discard(key)


def strip_fillers(text: str) -> str:
    """Agora prepends the filler phrase to the reply transcript ("Let me check that.The display shows...")."""
    from .agora_session import FILLER_PHRASES
    out = text.strip()
    changed = True
    while changed:
        changed = False
        for p in FILLER_PHRASES:
            if out.lower().startswith(p.lower()):
                out = out[len(p):].lstrip()
                changed = True
    return out


def _first_sentences(text: str, limit: int = 180) -> str:
    out = ""
    for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
        if len(out) + len(sent) > limit and out:
            break
        out = f"{out} {sent}".strip()
    return out[:limit]


def should_capture(session_id: str, turn_id: str) -> tuple[bool, str]:
    conn = connect()
    try:
        row = conn.execute("SELECT text FROM transcripts WHERE session_id=? AND role='agent' AND turn_id=?", (session_id, turn_id)).fetchone()
        agent_text = strip_fillers(row["text"]) if row else ""
        user = conn.execute(
            "SELECT text, ts FROM transcript_events WHERE session_id=? AND role='user' AND final=1 ORDER BY id DESC LIMIT 1", (session_id,)
        ).fetchone()
        # Did the agent itself record what it saw in THIS turn (since the technician's latest question)?
        # A fixed 20 s window wrongly suppressed back-to-back camera questions (21 Nov run).
        recent_visual = conn.execute(
            "SELECT ts FROM evidence WHERE session_id=? AND event_type='visual_observation' AND ts>=? ORDER BY id DESC LIMIT 1",
            (session_id, user["ts"] if user else utcnow()),
        ).fetchone()
    finally:
        conn.close()
    if not agent_text or not user or not CAMERA_Q.search(user["text"]) or not VISUAL_A.search(agent_text):
        return False, agent_text
    if recent_visual:
        return False, agent_text  # the agent recorded it itself
    return True, agent_text


async def on_agent_utterance(session_id: str, turn_id: str) -> None:
    key = (session_id, turn_id)
    if key in _scheduled:
        return
    _scheduled.add(key)
    await asyncio.sleep(DELAY_S)  # let the full sentence arrive and the agent's own tool call land
    ok, text = should_capture(session_id, turn_id)
    if not text:
        # Only the filler phrase has arrived for this turn; the real answer (often >3.5 s for vision) is still
        # coming. Re-arm so the next transcript update for this turn is evaluated (21 Nov: 4/12 vision turns missed).
        _scheduled.discard(key)
        return
    if not ok:
        return
    with tx() as conn:
        s = conn.execute("SELECT asset_id FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        ev = svc.record_evidence(
            conn, session_id=session_id, asset_id=s["asset_id"] if s else svc.fallback_asset_id(conn), event_type="visual_observation",
            source_type="camera_model", status="unverified", title=_first_sentences(text),
            detail=f"{text}\n\n(Captured from the agent's spoken description of the camera view; the agent did not record it itself.)",
            model_id=svc.VISION_MODEL_LABEL, media_ref=media.latest_snapshot(session_id, max_age_s=30),
            payload={"captured_by": "transcript", "turn_id": turn_id})
    bus.publish("evidence", {"id": ev["id"]})
