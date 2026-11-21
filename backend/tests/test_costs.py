"""Running cost: usage is metered per session, idle pause stops the meter, projections follow the site settings."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import costs
from app.api import create_app
from app.db import tx, utcnow


def _iso(dt):
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def _session(sid="S-1001"):
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status, task_id) VALUES (?,?,?,?,?,?,?)",
                     (sid, "C-204", "Kavya Rao", "A shift", utcnow(), "ACTIVE", "troubleshoot"))
    return sid


def test_estimate_counts_agent_minutes_camera_minutes_speech_and_turns():
    sid = _session()
    now = datetime.now(timezone.utc)
    with tx() as conn:
        conn.execute("INSERT INTO usage_segments(session_id, kind, started_at, ended_at) VALUES (?,?,?,?)", (sid, "voice", _iso(now - timedelta(minutes=10)), _iso(now - timedelta(minutes=4))))
        conn.execute("INSERT INTO usage_segments(session_id, kind, started_at, ended_at) VALUES (?,?,?,?)", (sid, "camera", _iso(now - timedelta(minutes=8)), _iso(now - timedelta(minutes=6))))
        for i in range(4):
            conn.execute("INSERT INTO transcripts(session_id, ts, role, turn_id, text) VALUES (?,?,?,?,?)", (sid, utcnow(), "agent", f"a{i}", "x" * 250))
    e = costs.estimate(sid)
    assert e["voice_minutes"] == 6.0 and e["camera_minutes"] == 2.0 and e["turns"] == 4 and e["agent_chars"] == 1000 and e["paused_now"]
    line = {x["item"]: x for x in e["lines"]}
    assert line["Agora agent task"]["qty"] == 6 and abs(line["Agora agent task"]["usd"] - 6 * 0.0099) < 1e-9
    assert line["Agora RTC video (camera on)"]["qty"] == 2.0 and line["Agora RTC audio"]["qty"] == 4.0
    assert abs(line["Murf Falcon voice"]["usd"] - 0.01) < 1e-9
    assert 0.1 < e["total_usd"] < 0.5


def test_settings_are_bounded_and_drive_the_projection():
    s = costs.settings_set({"idle_pause_min": 99, "camera_mode": "on_demand", "camera_share": 0.25, "active_min_per_shift": 30, "bogus": 1})
    assert float(s["idle_pause_min"]) == 30 and s["camera_mode"] == "on_demand" and "bogus" not in s
    p = costs.projection()
    assert p["per_shift_usd"] == round(p["per_active_minute_usd"] * 30, 2)
    assert p["always_on_8h_shift_usd"] > 10 * p["per_shift_usd"]  # streaming all shift would cost far more than sessions
    costs.settings_set({"camera_mode": "always"})
    assert costs.projection()["per_active_minute_usd"] > p["per_active_minute_usd"]  # camera on all the time costs more


def test_pause_stops_the_meter_and_is_recorded():
    sid = _session()
    costs.segment_start(sid, "voice")
    costs.segment_start(sid, "camera")
    c = TestClient(create_app())
    r = c.post(f"/api/sessions/{sid}/voice/pause", json={"reason": "idle", "idle_min": 3})
    assert r.status_code == 200
    assert costs.estimate(sid)["paused_now"] is True
    ev = c.get(f"/api/sessions/{sid}").json()["evidence"]
    assert any("paused after 3 min of silence" in e["title"] for e in ev)
