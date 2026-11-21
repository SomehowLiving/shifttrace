"""Running cost: what a voice session costs, and the controls that keep it low.

Nothing streams "all the time". An Agora agent exists only while a worker is in a session; it is paused automatically
after a few minutes of silence (no agent minutes while paused) and ended with the session. The camera can be on demand,
so most minutes are billed as audio, not video. This module estimates the cost of each session from what was actually
used (agent minutes, camera minutes, characters spoken, turns) and projects it per worker per shift.

Rates are public list prices at the time of writing and are overridable in backend/.env (COST_*). They are estimates:
the real bill depends on the Agora / Murf / LLM contract, and whether the managed LLM is billed through Agora.
"""
from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from typing import Any

from .db import connect, parse_ts, rows_to_dicts, tx, utcnow


def _rate(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


RATES = [  # key, label, default, unit, source
    ("COST_CONVOAI_PER_MIN", "Agora Conversational AI, agent task", 0.0099, "per agent minute", "docs.agora.io Conversational AI pricing (audio basic task)"),
    ("COST_ASR_PER_MIN", "Agora ASR (speech to text)", 0.0166, "per agent minute", "docs.agora.io Conversational AI pricing (ARES ASR task)"),
    ("COST_RTC_AUDIO_PER_MIN", "Agora RTC, audio", 0.00099, "per participant minute", "agora.io voice calling list price ($0.99 / 1,000 min)"),
    ("COST_RTC_VIDEO_PER_MIN", "Agora RTC, HD video", 0.00399, "per participant minute with camera on", "agora.io video calling list price ($3.99 / 1,000 min)"),
    ("COST_TTS_PER_1K_CHARS", "Murf Falcon voice", 0.01, "per 1,000 characters spoken", "murf.ai Falcon API docs ($0.01 / 1,000 characters)"),
    ("COST_LLM_IN_PER_M", "LLM input (gpt-4o-mini)", 0.15, "per million input tokens", "OpenAI list price; may be billed through Agora when managed"),
    ("COST_LLM_OUT_PER_M", "LLM output (gpt-4o-mini)", 0.60, "per million output tokens", "OpenAI list price; may be billed through Agora when managed"),
]
PROMPT_TOKENS, TOKENS_PER_TURN_GROWTH, OUTPUT_TOKENS, IMAGE_TOKENS = 2600, 180, 70, 850  # estimates per LLM turn

DEFAULT_SETTINGS = {"idle_pause_min": "3", "camera_mode": "always", "max_session_min": "60", "active_min_per_shift": "40", "camera_share": "0.3"}


def rates() -> dict[str, float]:
    return {k: _rate(k, d) for k, _, d, _, _ in RATES}


def settings_get() -> dict[str, str]:
    conn = connect()
    try:
        rows = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM site_settings").fetchall()}
    finally:
        conn.close()
    return {**DEFAULT_SETTINGS, **rows}


def settings_set(values: dict[str, Any]) -> dict[str, str]:
    allowed = {"idle_pause_min": (0, 30), "max_session_min": (5, 480), "active_min_per_shift": (1, 480), "camera_share": (0, 1)}
    with tx() as conn:
        for k, v in values.items():
            if k == "camera_mode":
                if v not in ("always", "on_demand"):
                    continue
                conn.execute("INSERT INTO site_settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
            elif k in allowed:
                lo, hi = allowed[k]
                num = min(hi, max(lo, float(v)))
                conn.execute("INSERT INTO site_settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, f"{num:g}"))
    return settings_get()


# --------------------------------------------------------------------------- usage tracking

def segment_start(session_id: str, kind: str = "voice") -> None:
    with tx() as conn:
        open_ = conn.execute("SELECT 1 FROM usage_segments WHERE session_id=? AND kind=? AND ended_at IS NULL", (session_id, kind)).fetchone()
        if not open_:
            conn.execute("INSERT INTO usage_segments(session_id, kind, started_at) VALUES (?,?,?)", (session_id, kind, utcnow()))


def segment_end(session_id: str, kind: str | None = None) -> None:
    with tx() as conn:
        if kind:
            conn.execute("UPDATE usage_segments SET ended_at=? WHERE session_id=? AND kind=? AND ended_at IS NULL", (utcnow(), session_id, kind))
        else:
            conn.execute("UPDATE usage_segments SET ended_at=? WHERE session_id=? AND ended_at IS NULL", (utcnow(), session_id))


def _minutes(rows: list[dict[str, Any]], kind: str) -> float:
    now = datetime.now(timezone.utc)
    secs = 0.0
    for r in rows:
        if r["kind"] != kind:
            continue
        end = parse_ts(r["ended_at"]) if r["ended_at"] else now
        secs += max(0.0, (end - parse_ts(r["started_at"])).total_seconds())
    return secs / 60


def estimate(session_id: str) -> dict[str, Any]:
    conn = connect()
    try:
        segs = rows_to_dicts(conn.execute("SELECT * FROM usage_segments WHERE session_id=?", (session_id,)).fetchall())
        agent_chars = conn.execute("SELECT IFNULL(sum(length(text)),0) FROM transcripts WHERE session_id=? AND role='agent'", (session_id,)).fetchone()[0]
        turns = conn.execute("SELECT count(*) FROM transcripts WHERE session_id=? AND role='agent'", (session_id,)).fetchone()[0]
    finally:
        conn.close()
    r = rates()
    voice_min = _minutes(segs, "voice")
    cam_min = min(voice_min, _minutes(segs, "camera"))
    billed_agent_min = sum(math.ceil(_minutes([s], "voice")) for s in segs if s["kind"] == "voice")  # Agora rounds each task up to a minute
    cam_share = cam_min / voice_min if voice_min else 0
    in_tok = sum(PROMPT_TOKENS + TOKENS_PER_TURN_GROWTH * min(i, 20) for i in range(turns)) + int(turns * cam_share * IMAGE_TOKENS)
    out_tok = turns * OUTPUT_TOKENS
    lines = [
        ("Agora agent task", billed_agent_min, "min", billed_agent_min * r["COST_CONVOAI_PER_MIN"]),
        ("Agora speech to text", billed_agent_min, "min", billed_agent_min * r["COST_ASR_PER_MIN"]),
        ("Agora RTC audio", max(0.0, voice_min - cam_min), "min", max(0.0, voice_min - cam_min) * r["COST_RTC_AUDIO_PER_MIN"]),
        ("Agora RTC video (camera on)", cam_min, "min", cam_min * r["COST_RTC_VIDEO_PER_MIN"]),
        ("Murf Falcon voice", agent_chars, "chars", agent_chars / 1000 * r["COST_TTS_PER_1K_CHARS"]),
        ("LLM (estimated tokens)", in_tok + out_tok, "tokens", in_tok / 1e6 * r["COST_LLM_IN_PER_M"] + out_tok / 1e6 * r["COST_LLM_OUT_PER_M"]),
    ]
    total = sum(x[3] for x in lines)
    return {"session_id": session_id, "voice_minutes": round(voice_min, 2), "camera_minutes": round(cam_min, 2), "turns": turns,
            "agent_chars": agent_chars, "lines": [{"item": a, "qty": round(b, 2), "unit": c, "usd": round(d, 4)} for a, b, c, d in lines],
            "total_usd": round(total, 4), "per_voice_minute_usd": round(total / voice_min, 4) if voice_min >= 1 else None,
            "paused_now": not any(s["kind"] == "voice" and not s["ended_at"] for s in segs)}


def projection() -> dict[str, Any]:
    """Cost per worker per shift and per month from the settings, using a typical turn rate."""
    s, r = settings_get(), rates()
    mins = float(s["active_min_per_shift"])
    cam = float(s["camera_share"]) if s["camera_mode"] == "on_demand" else 1.0
    turns_per_min, chars_per_turn = 2.0, 160
    per_min = (r["COST_CONVOAI_PER_MIN"] + r["COST_ASR_PER_MIN"] + (1 - cam) * r["COST_RTC_AUDIO_PER_MIN"] + cam * r["COST_RTC_VIDEO_PER_MIN"]
               + turns_per_min * chars_per_turn / 1000 * r["COST_TTS_PER_1K_CHARS"]
               + turns_per_min * ((PROMPT_TOKENS + 10 * TOKENS_PER_TURN_GROWTH + cam * IMAGE_TOKENS) / 1e6 * r["COST_LLM_IN_PER_M"] + OUTPUT_TOKENS / 1e6 * r["COST_LLM_OUT_PER_M"]))
    always_on = 8 * 60 * (r["COST_CONVOAI_PER_MIN"] + r["COST_ASR_PER_MIN"] + r["COST_RTC_VIDEO_PER_MIN"])
    return {"settings": s, "per_active_minute_usd": round(per_min, 4), "per_shift_usd": round(per_min * mins, 2),
            "per_month_usd": round(per_min * mins * 22, 2), "always_on_8h_shift_usd": round(always_on, 2),
            "assumptions": f"{mins:g} active voice minutes per shift, camera on {int(cam * 100)}% of them, ~{turns_per_min:g} agent turns per minute, 22 shifts a month",
            "rates": [{"key": k, "label": label, "value": rates()[k], "unit": unit, "source": src} for k, label, _, unit, src in RATES]}
