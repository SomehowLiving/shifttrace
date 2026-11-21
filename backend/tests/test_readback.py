"""record_observation and update_open_item re-read their write on a fresh connection, like every other mutation."""
from app import guard, tools
from app.db import connect, tx

from test_workflow import agent_says, call, start_session


def _last_action(name):
    conn = connect()
    try:
        return conn.execute("SELECT status FROM tool_actions WHERE tool_name=? ORDER BY id DESC LIMIT 1", (name,)).fetchone()["status"]
    finally:
        conn.close()


def test_record_observation_is_verified_by_readback():
    sid = start_session()
    r = call("record_observation", sid, lambda c: tools.record_observation(c, "technician_report", "Coupling guard is warm", None))
    assert r["ok"] and r["verified"] is True
    conn = connect()
    try:
        row = conn.execute("SELECT title, source_type FROM evidence WHERE id=?", (r["event_id"],)).fetchone()
    finally:
        conn.close()
    assert row["title"] == "Coupling guard is warm" and row["source_type"] == "technician"
    assert _last_action("record_observation") == "ok"


def test_update_open_item_is_verified_by_readback():
    sid = start_session()
    with tx() as conn:
        q = conn.execute("SELECT id FROM evidence WHERE title LIKE 'Does vibration rise%'").fetchone()["id"]
    r = call("update_open_item", sid, lambda c: tools.update_open_item(c, q, "answered", "Vibration came first"))
    assert r["ok"] and r["verified"] is True and r["status"] == "answered"


def test_failed_readback_is_reported_as_failure_and_claim_is_flagged(monkeypatch):
    sid = start_session()
    monkeypatch.setattr(tools, "_verify", lambda sql, params, check: (False, None))
    r = call("record_observation", sid, lambda c: tools.record_observation(c, "technician_report", "Belt is glazed", None))
    assert r["ok"] is False and r["verified"] is False and "may not be stored" in r["message"]
    assert _last_action("record_observation") == "error"
    with tx() as conn:
        q = conn.execute("SELECT id FROM evidence WHERE title LIKE 'Coupling alignment%'").fetchone()["id"]
    r = call("update_open_item", sid, lambda c: tools.update_open_item(c, q, "answered", "checked"))
    assert r["ok"] is False and _last_action("update_open_item") == "error"
    # With no successful write behind it, "I've recorded that" is caught by the claim guard.
    agent_says(sid, "I've recorded that the belt is glazed.", "a1")
    assert ("recorded", "I've recorded that the belt is glazed.") in guard.find_violations(sid, "I've recorded that the belt is glazed.")
