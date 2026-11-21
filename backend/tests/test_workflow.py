"""End-to-end workflow through the same tool functions Agora calls (minus the network)."""
import asyncio

import pytest

from app import services as svc, tools
from app.db import connect, tx, utcnow


def run(coro):
    return asyncio.run(coro)


def start_session(technician="Kavya Rao"):
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status) VALUES (?,?,?,?,?,?)",
                     ("S-1001", "C-204", technician, "A shift", utcnow(), "ACTIVE"))
    return "S-1001"


def say(session_id, text, turn, role="user", final=True):
    with tx() as conn:
        svc.add_transcript(conn, session_id, role, turn, text, final)


def agent_says(session_id, text, turn):
    say(session_id, text, turn, role="agent")


def call(name, sid, impl, **args):
    return run(tools.run_tool(name, args, sid, "test", impl))


def test_history_and_previous_handoff():
    sid = start_session()
    h = call("get_asset_history", sid, lambda c: tools.get_asset_history(c, None))
    assert h["ok"] and h["asset"]["asset_id"] == "C-204"
    assert any(w["work_order_id"] == "WO-1187" for w in h["work_orders"])
    prev = call("get_previous_handoff", sid, lambda c: tools.get_previous_handoff(c, None))
    assert prev["handoff_id"] == "H-0042"
    assert any("Coupling" in loop for loop in prev["open_loops"])
    assert prev["ruled_out"] == ["Sensor TS-2 is the cause of A-17"]


def test_manual_search_ranks_relevant_section():
    sid = start_session()
    r = call("search_maintenance_manual", sid, lambda c: tools.search_maintenance_manual(c, "A-17 came back after replacing the sensor", None))
    assert r["sections"][0]["section"] == "4.2"
    r = call("search_maintenance_manual", sid, lambda c: tools.search_maintenance_manual(c, "drive end bearing vibration limit", None))
    assert r["sections"][0]["section"] == "6.3"


def test_inventory_resolution():
    sid = start_session()
    r = call("check_inventory", sid, lambda c: tools.check_inventory(c, "drive end bearing"))
    assert [m["part_id"] for m in r["matches"]] == ["BRG-6316-C3"] and r["matches"][0]["available"] == 0
    r = call("check_inventory", sid, lambda c: tools.check_inventory(c, "non-drive end bearing"))
    assert r["matches"][0]["part_id"] == "BRG-6314-C3"
    r = call("check_inventory", sid, lambda c: tools.check_inventory(c, "BRG-6316-C3"))
    assert len(r["matches"]) == 1
    r = call("check_inventory", sid, lambda c: tools.check_inventory(c, "flux capacitor"))
    assert r["ok"] is False and r["error"] == "part_not_found"


def test_procurement_requires_spoken_approval_and_is_idempotent():
    sid = start_session()
    say(sid, "Yes, go ahead and order it", "early")  # said BEFORE the draft existed: must not count
    d = call("create_procurement_request", sid, lambda c: tools.create_procurement_request(c, "BRG-6316-C3", 1, None, "DE bearing suspected"))
    assert d["status"] == "PENDING_APPROVAL" and d["request_id"] == "PR-2001"
    dup = call("create_procurement_request", sid, lambda c: tools.create_procurement_request(c, "BRG-6316-C3", 1, None, None))
    assert dup["duplicate"] and dup["request_id"] == "PR-2001"

    r = call("approve_procurement_request", sid, lambda c: tools.approve_procurement_request(c, "PR-2001"))
    assert r["status"] == "APPROVAL_REQUIRED" and r["ok"] is False

    # The request utterance can be relayed AFTER the draft exists; without a read-back it must not count.
    say(sid, "Prepare the order and submit it", "late")
    r = call("approve_procurement_request", sid, lambda c: tools.approve_procurement_request(c, "PR-2001"))
    assert r["status"] == "APPROVAL_REQUIRED"

    agent_says(sid, "Draft PR 2001: one drive end bearing for work order 1187. Shall I submit it?", "a1")
    say(sid, "No, wait.", "t1")
    r = call("approve_procurement_request", sid, lambda c: tools.approve_procurement_request(c, "PR-2001"))
    assert r["status"] == "APPROVAL_REQUIRED"

    say(sid, "Yes, submit it.", "t2")
    r = call("approve_procurement_request", sid, lambda c: tools.approve_procurement_request(c, "PR-2001"))
    assert r["ok"] and r["verified"] and r["status"] == "SUBMITTED" and r["expected_by"]
    assert "Yes, submit it." in r["approval_evidence"]

    again = call("approve_procurement_request", sid, lambda c: tools.approve_procurement_request(c, "PR-2001"))
    assert again["duplicate"] is True
    conn = connect()
    try:
        assert conn.execute("SELECT count(*) FROM procurement_requests WHERE session_id=?", (sid,)).fetchone()[0] == 1
        audit = conn.execute("SELECT tool_name, status FROM tool_actions ORDER BY id").fetchall()
    finally:
        conn.close()
    assert ("approve_procurement_request", "approval_required") in [tuple(a) for a in audit]


def test_supplier_rejection_is_reported_not_claimed():
    sid = start_session()
    with tx() as conn:
        conn.execute("UPDATE demo_flags SET enabled=1 WHERE flag='supplier_rejects'")
    call("create_procurement_request", sid, lambda c: tools.create_procurement_request(c, "BRG-6316-C3", 1, None, None))
    agent_says(sid, "Shall I submit it?", "a1")
    say(sid, "yes please submit", "t1")
    r = call("approve_procurement_request", sid, lambda c: tools.approve_procurement_request(c, "PR-2001"))
    assert r["ok"] is False and r["verified"] is False and r["status"] == "REJECTED"
    assert "NOT placed" in r["message"]


def test_inventory_outage():
    sid = start_session()
    with tx() as conn:
        conn.execute("UPDATE demo_flags SET enabled=1 WHERE flag='inventory_outage'")
    r = call("check_inventory", sid, lambda c: tools.check_inventory(c, "bearing"))
    assert r["ok"] is False and r["error"] == "inventory_unavailable"


def test_work_order_transitions():
    sid = start_session()
    r = call("update_work_order", sid, lambda c: tools.update_work_order(c, None, "WAITING_PARTS", "Waiting for PR-2001"))
    assert r["verified"] and r["status"] == "WAITING_PARTS"
    r = call("update_work_order", sid, lambda c: tools.update_work_order(c, "WO-1187", "RESOLVED", "done"))
    assert r["ok"] is False and r["error"] == "bad_transition"
    call("update_work_order", sid, lambda c: tools.update_work_order(c, "WO-1187", "IN_PROGRESS", "bearing arrived"))
    r = call("update_work_order", sid, lambda c: tools.update_work_order(c, "WO-1187", "RESOLVED", "fixed"))
    assert r["ok"] is False and r["error"] == "needs_signoff"


def test_reservation_idempotent_and_stock_checked():
    sid = start_session()
    r1 = call("reserve_spare_part", sid, lambda c: tools.reserve_spare_part(c, "CPL-INS-90", 1, None))
    r2 = call("reserve_spare_part", sid, lambda c: tools.reserve_spare_part(c, "CPL-INS-90", 1, None))
    assert r1["verified"] and not r1["duplicate"] and r2["duplicate"]
    r3 = call("reserve_spare_part", sid, lambda c: tools.reserve_spare_part(c, "BRG-6316-C3", 1, None))
    assert r3["ok"] is False and r3["error"] == "insufficient_stock"


def test_handoff_built_from_records_and_next_shift_reads_it():
    sid = start_session()
    call("record_observation", sid, lambda c: tools.record_observation(c, "visual", "TEMP HIGH lamp appears lit, display A-17 108 C", None))
    call("record_observation", sid, lambda c: tools.record_observation(c, "technician_report", "Vibration started before the warning", "Kavya: it shook first"))
    with tx() as conn:
        q = conn.execute("SELECT id FROM evidence WHERE title LIKE 'Does vibration rise%'").fetchone()["id"]
    call("update_open_item", sid, lambda c: tools.update_open_item(c, q, "answered", "Kavya saw vibration rise first"))
    call("check_inventory", sid, lambda c: tools.check_inventory(c, "BRG-6316-C3"))
    call("create_procurement_request", sid, lambda c: tools.create_procurement_request(c, "BRG-6316-C3", 1, None, None))
    agent_says(sid, "Shall I submit it?", "a9")
    say(sid, "yes", "t9")
    call("approve_procurement_request", sid, lambda c: tools.approve_procurement_request(c, "PR-2001"))
    call("update_work_order", sid, lambda c: tools.update_work_order(c, None, "WAITING_PARTS", "Bearing ordered PR-2001"))
    h = call("create_shift_handoff", sid, lambda c: tools.create_shift_handoff(c))
    assert h["verified"] and h["handoff_id"] == "H-0043"
    assert all("Does vibration rise" not in loop for loop in h["open_loops"])
    assert any("Coupling" in loop for loop in h["open_loops"])

    with tx() as conn:
        conn.execute("UPDATE sessions SET status='ENDED' WHERE session_id=?", (sid,))
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status) VALUES ('S-1002','C-204','Dev Malhotra','B shift',?, 'ACTIVE')", (utcnow(),))
    nxt = call("get_previous_handoff", "S-1002", lambda c: tools.get_previous_handoff(c, None))
    assert nxt["handoff_id"] == "H-0043" and nxt["created_by"] == "Kavya Rao"
    assert any("PR-2001" in a for a in nxt["actions_completed"])
    assert any("TEMP HIGH" in o["text"] and o["source"] == "camera_model" for o in nxt["observations"])
    assert nxt["work_order"]["status"] == "WAITING_PARTS"


def test_affirmative_detection():
    assert svc.is_affirmative("Yes, submit it")
    assert svc.is_affirmative("okay go ahead")
    assert not svc.is_affirmative("no don't submit")
    assert not svc.is_affirmative("wait, hold on")
    assert not svc.is_affirmative("what's the lead time?")


def test_spoken_id_forms_are_accepted():
    """Live run: the LLM passed '1187' instead of 'WO-1187' and the draft failed."""
    sid = start_session()
    d = call("create_procurement_request", sid, lambda c: tools.create_procurement_request(c, "BRG-6316-C3", 1, "1187", None))
    assert d["ok"] and d["request"]["work_order_id"] == "WO-1187"
    agent_says(sid, "Shall I submit it?", "a1")
    say(sid, "yes", "t1")
    r = call("approve_procurement_request", sid, lambda c: tools.approve_procurement_request(c, "2001"))
    assert r["verified"] and r["request_id"] == "PR-2001"
    r = call("update_work_order", sid, lambda c: tools.update_work_order(c, "wo 1187", "WAITING_PARTS", "ordered"))
    assert r["verified"] and r["work_order_id"] == "WO-1187"
    assert svc.normalize_asset("c 204") == "C-204" and svc.normalize_asset("C204") == "C-204"


def test_asset_id_passed_as_work_order_or_request_id():
    """Live run: the LLM passed 'C-204' as work_order_id and then as request_id."""
    assert svc.normalize_id("C-204", "WO") == "C-204" and svc.normalize_id("work order 1187", "WO") == "WO-1187"
    sid = start_session()
    d = call("create_procurement_request", sid, lambda c: tools.create_procurement_request(c, "BRG-6316-C3", 1, "C-204", None))
    assert d["ok"] and d["request"]["work_order_id"] == "WO-1187" and "not found" in d["note"]
    agent_says(sid, "Shall I submit it?", "a1")
    say(sid, "yes", "t1")
    r = call("approve_procurement_request", sid, lambda c: tools.approve_procurement_request(c, "C-204"))
    assert r["verified"] and r["request_id"] == "PR-2001"
