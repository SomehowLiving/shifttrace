"""Beyond maintenance: warehouse and logistics, follow-ups, training and onboarding (same rules: spoken yes, re-read, code decides)."""
import asyncio
from datetime import datetime, timedelta, timezone

from app import guard, packs, services as svc, tools, workplace as wp
from app.agora_session import build_instructions
from app.db import connect, tx, utcnow
from app.mcp_server import CORE_TOOLS, DOMAIN_TOOLS, TOOL_NAMES

WH = "DC2-ZB"


def _session(sid="S-1001", asset=WH, task="warehouse_ops", who="Kavya Rao") -> str:
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status, task_id) VALUES (?,?,?,?,?,?,?)",
                     (sid, asset, who, "A shift", utcnow(), "ACTIVE", task))
    return sid


def call(name, sid, impl, **args):
    return asyncio.run(tools.run_tool(name, args, sid, "test", impl))


def say(sid, role, text, turn):
    with tx() as conn:
        svc.add_transcript(conn, sid, role, turn, text, True)


def level(part, loc):
    conn = connect()
    try:
        return conn.execute("SELECT quantity FROM stock_levels WHERE part_id=? AND location=?", (part, loc)).fetchone()["quantity"]
    finally:
        conn.close()


def test_tool_sets():
    assert set(DOMAIN_TOOLS) & set(CORE_TOOLS) == set() and len(TOOL_NAMES) == len(CORE_TOOLS) + len(DOMAIN_TOOLS)
    wh = packs.allowed_tools(packs.get_task("warehouse_ops"))
    assert {"track_shipment", "create_stock_transfer", "confirm_stock_transfer", "schedule_follow_up"} <= set(wh)
    assert "create_stock_transfer" not in packs.allowed_tools(packs.get_task("troubleshoot"))
    assert "finish_training_module" in packs.allowed_tools(packs.get_task("onboarding"))


def test_prompts_follow_persona_and_task():
    conn = connect()
    try:
        zone, c204 = svc.get_asset(conn, WH), svc.get_asset(conn, "C-204")
    finally:
        conn.close()
    t = build_instructions(zone, "Kavya Rao", "A shift", packs.get_task("warehouse_ops"))
    assert "associate Kavya Rao" in t and "warehouse and ERP systems" in t and "Shall I move it?" in t and "eye contact" in t
    assert "cannot order" not in t
    o = build_instructions(c204, "Kavya Rao", "A shift", packs.get_task("onboarding"))
    assert "record_training_answer" in o and "Never mark an answer yourself" in o and "technician Kavya Rao" in o
    b = build_instructions(c204, "Kavya Rao", "A shift", packs.get_task("shift_briefing"))
    assert "cannot order, reserve, move stock" in b
    assert "cannot order" not in build_instructions(c204, "Kavya Rao", "A shift", packs.get_task("troubleshoot"))


def test_inventory_shows_stock_per_location_and_shipment_tracking():
    sid = _session()
    inv = call("check_inventory", sid, lambda c: tools.check_inventory(c, "basmati rice"))
    locs = {x["location"]: x["quantity"] for x in inv["matches"][0]["locations"]}
    assert locs == {"B-04-2": 2, "R-12": 40}
    by_id = call("track_shipment", sid, lambda c: tools.track_shipment(c, "4471"))
    assert by_id["shipments"][0]["shipment_id"] == "SHP-4471" and by_id["shipments"][0]["status"] == "DELAYED"
    assert by_id["shipments"][0]["recent_events"][0]["status"] == "IN_TRANSIT"
    by_item = call("track_shipment", sid, lambda c: tools.track_shipment(c, "the rice delivery"))
    assert "SHP-4471" in [s["shipment_id"] for s in by_item["shipments"]]


def test_stock_transfer_needs_spoken_yes_then_moves_stock_and_posts_to_erp():
    sid = _session()
    d = call("create_stock_transfer", sid, lambda c: tools.create_stock_transfer(c, "SKU-2231", 20, "reserve R twelve", "bin B 04 2", "below min"))
    assert d["verified"] and d["status"] == "PENDING_CONFIRMATION" and d["transfer"]["from_location"] == "R-12" and d["transfer"]["to_location"] == "B-04-2"
    tid = d["transfer_id"]
    # the model cannot confirm its own action: no read-back and no yes -> nothing moves
    r = call("confirm_stock_transfer", sid, lambda c: tools.confirm_stock_transfer(c, tid))
    assert r["status"] == "APPROVAL_REQUIRED" and level("SKU-2231", "B-04-2") == 2
    # a yes spoken BEFORE the read-back does not count
    say(sid, "user", "yes move it", "u1")
    r = call("confirm_stock_transfer", sid, lambda c: tools.confirm_stock_transfer(c, tid))
    assert r["status"] == "APPROVAL_REQUIRED"
    say(sid, "agent", "Twenty cases of basmati rice from R 12 to B 04 2. Shall I move it?", "a1")
    say(sid, "user", "Yes, move it.", "u2")
    r = call("confirm_stock_transfer", sid, lambda c: tools.confirm_stock_transfer(c, tid))
    assert r["ok"] and r["verified"] and r["status"] == "DONE" and r["erp_ref"].startswith("ERP-")
    assert level("SKU-2231", "B-04-2") == 22 and level("SKU-2231", "R-12") == 20
    assert r["stock_now"] == {"R-12": 20, "B-04-2": 22}
    again = call("confirm_stock_transfer", sid, lambda c: tools.confirm_stock_transfer(c, tid))
    assert again["duplicate"] and level("SKU-2231", "B-04-2") == 22  # nothing moved twice


def test_transfer_refuses_more_than_is_there():
    sid = _session()
    r = call("create_stock_transfer", sid, lambda c: tools.create_stock_transfer(c, "SKU-2231", 60, "R-12", "B-04-2", None))
    assert r["ok"] is False and r["error"] == "insufficient_stock"


def test_follow_up_is_scheduled_with_a_due_date_and_verified():
    sid = _session()
    r = call("schedule_follow_up", sid, lambda c: tools.schedule_follow_up(c, "Recount B-06-1 with a second associate", "next shift", "Dev Malhotra"))
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    assert r["verified"] and r["due"] == tomorrow and r["assignee"] == "Dev Malhotra" and r["follow_up_id"] == "FU-5001"
    assert wp.parse_due("2026-12-01") == "2026-12-01" and wp.parse_due("whenever") is None


def test_training_is_marked_in_code_and_updates_the_learning_record():
    sid = _session(asset="C-204", task="onboarding", who="Dev Malhotra")
    m = call("get_training_module", sid, lambda c: tools.get_training_module(c, None))
    assert m["module_id"] == "KS75-SAFE-1" and len(m["questions"]) == 3
    assert all("key_points" not in q for q in m["questions"])  # the model is not given the marking key
    a1 = call("record_training_answer", sid, lambda c: tools.record_training_answer(c, "q1", "I lock out and tag out the drive and check there is zero energy", None))
    a2 = call("record_training_answer", sid, lambda c: tools.record_training_answer(c, "q2", "A seventeen means the discharge temperature is high", None))
    a3 = call("record_training_answer", sid, lambda c: tools.record_training_answer(c, "q3", "Above about five millimetres per second I think", None))
    assert (a1["result"], a2["result"], a3["result"]) == ("correct", "partly", "incorrect")
    assert "115" in a2["missing_key_points"] and a3["section"] == "6.3"
    f = call("finish_training_module", sid, lambda c: tools.finish_training_module(c, None))
    assert f["verified"] and f["score"] == 50 and f["status"] == "NEEDS_REVIEW" and not f["passed"]
    assert {r["question_id"] for r in f["review"]} == {"q2", "q3"}
    # second attempt in the same session: improved answers pass
    call("record_training_answer", sid, lambda c: tools.record_training_answer(c, "q2", "Discharge temperature high, shutdown at 115 degrees", None))
    call("record_training_answer", sid, lambda c: tools.record_training_answer(c, "q3", "Seven point one, plan a bearing replacement", None))
    f2 = call("finish_training_module", sid, lambda c: tools.finish_training_module(c, None))
    assert f2["score"] == 100 and f2["status"] == "PASSED"
    conn = connect()
    try:
        rec = conn.execute("SELECT * FROM learning_records WHERE trainee='Dev Malhotra' AND module_id='KS75-SAFE-1'").fetchone()
    finally:
        conn.close()
    assert rec["status"] == "PASSED" and rec["attempts"] == 2


def test_handoff_includes_transfers_training_and_follow_ups():
    sid = _session()
    d = call("create_stock_transfer", sid, lambda c: tools.create_stock_transfer(c, "SKU-2231", 20, "R-12", "B-04-2", None))
    say(sid, "agent", "Shall I move it?", "a1")
    say(sid, "user", "yes", "u1")
    call("confirm_stock_transfer", sid, lambda c: tools.confirm_stock_transfer(c, d["transfer_id"]))
    call("schedule_follow_up", sid, lambda c: tools.schedule_follow_up(c, "Chase SHP-4471 with the carrier", "today", None))
    h = call("create_shift_handoff", sid, lambda c: tools.create_shift_handoff(c))
    conn = connect()
    try:
        import json
        rep = json.loads(conn.execute("SELECT report_json FROM handoffs WHERE handoff_id=?", (h["handoff_id"],)).fetchone()[0])
    finally:
        conn.close()
    assert any("Stock transfer TR-6001" in a["text"] and "ERP" in a["detail"] for a in rep["actions_completed"])
    assert rep["follow_ups"][0]["title"] == "Chase SHP-4471 with the carrier"
    assert "Follow-up scheduled" in rep["spoken_summary"]


def test_claim_guard_covers_new_actions():
    sid = _session()
    assert ("transferred", "The stock has been moved to B-04-2.") in guard.find_violations(sid, "The stock has been moved to B-04-2.")
    assert ("follow_up", "I've scheduled a follow-up for the recount.") in guard.find_violations(sid, "I've scheduled a follow-up for the recount.")
    call("schedule_follow_up", sid, lambda c: tools.schedule_follow_up(c, "Recount B-06-1", "tomorrow", None))
    assert not [v for v in guard.find_violations(sid, "I've scheduled a follow-up for the recount.") if v[0] == "follow_up"]


def test_task_allowlist_blocks_domain_tools_outside_their_task():
    sid = _session(asset="C-204", task="troubleshoot")
    r = asyncio.run(tools.run_tool("create_stock_transfer", {}, sid, "agora_mcp",
                                   lambda c: tools.create_stock_transfer(c, "SKU-2231", 1, "R-12", "B-04-2", None)))
    assert r["error"] == "not_available_in_task" and level("SKU-2231", "R-12") == 40


def test_split_asr_reply_is_read_together_but_latest_words_decide():
    sid = _session()
    d = call("create_stock_transfer", sid, lambda c: tools.create_stock_transfer(c, "SKU-2231", 5, "R-12", "B-04-2", None))
    say(sid, "agent", "Five cases from R 12 to B 04 2. Shall I move it?", "a1")
    say(sid, "user", "Yes.", "u1")
    say(sid, "user", "No, wait.", "u2")  # changed their mind: latest words decide
    r = call("confirm_stock_transfer", sid, lambda c: tools.confirm_stock_transfer(c, d["transfer_id"]))
    assert r["status"] == "APPROVAL_REQUIRED"
    say(sid, "agent", "Okay. Shall I move it now?", "a2")
    say(sid, "user", "Yes.", "u3")
    say(sid, "user", "Do the transfer please.", "u4")  # one reply split by ASR: read together
    r = call("confirm_stock_transfer", sid, lambda c: tools.confirm_stock_transfer(c, d["transfer_id"]))
    assert r["status"] == "DONE" and level("SKU-2231", "B-04-2") == 7
