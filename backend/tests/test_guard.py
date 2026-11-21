"""Claim guard: agent statements must be backed by successful tool calls."""
from app import guard, services as svc
from app.db import tx, utcnow


def _session():
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status) VALUES ('S-1001','C-204','Kavya Rao','A shift',?, 'ACTIVE')", (utcnow(),))
    return "S-1001"


def _tool(sid, name, status="ok"):
    with tx() as conn:
        svc.log_tool_action(conn, sid, name, "agora_mcp", {}, {}, status, 10)


def cats(sid, text):
    return [c for c, _ in guard.find_violations(sid, text)]


def test_flags_the_exact_hallucinations_seen_live():
    sid = _session()
    assert cats(sid, "The procurement request for one drive end bearing has been submitted successfully.") == ["order_submitted"]
    assert cats(sid, "The work order has been successfully updated.") == ["wo_updated"]
    assert "manual" in cats(sid, "The manual, section 7.2, states that an A-17 alarm may indicate a malfunction.")
    assert "inventory" in cats(sid, "The inventory tool says the drive end bearing is currently out of stock.")
    assert "history" in cats(sid, "The previous technician reported a high discharge temperature at 108 degrees.")


def test_backed_claims_pass():
    sid = _session()
    _tool(sid, "approve_procurement_request")
    _tool(sid, "check_inventory")
    _tool(sid, "search_maintenance_manual")
    assert cats(sid, "PR 2001 has been submitted to the supplier.") == []
    assert cats(sid, "It is out of stock in Stores A-14.") == []
    assert cats(sid, "The manual, section 4.2, says the sensor is unlikely to be the cause.") == []


def test_failed_tool_does_not_back_a_claim():
    sid = _session()
    _tool(sid, "approve_procurement_request", status="approval_required")
    assert cats(sid, "The order has been submitted.") == ["order_submitted"]


def test_questions_and_negations_are_not_claims():
    sid = _session()
    assert cats(sid, "I've drafted nothing yet. Shall I submit it?") == []
    assert cats(sid, "It has not been submitted.") == []
    assert cats(sid, "Would you like me to update the work order?") == []


def test_greeting_and_invitations_are_not_claims():
    import asyncio
    sid = _session()
    # before the technician speaks, nothing is checked (the greeting)
    assert asyncio.run(guard.check_agent_utterance(sid, "1", "Kavya, ask me what happened on the previous shift.")) == []
    assert cats(sid, "Kavya, ask me what happened on the previous shift, or point your camera at the panel.") == []


def test_outage_claims_need_a_real_failure():
    sid = _session()
    assert cats(sid, "I can't reach the maintenance system right now, so that was not done.") == ["false_outage"]
    _tool(sid, "check_inventory", status="error")
    assert cats(sid, "I can't reach the inventory system right now.") == []


def test_next_shift_can_describe_state_read_from_records():
    """Live run: 'WO-1187 is now waiting for parts' (read from the handoff) was flagged and the correction
    made the agent update the work order unasked."""
    sid = _session()
    assert cats(sid, "The work order WO-1187 is now waiting for parts.") == ["wo_updated"]
    _tool(sid, "get_previous_handoff")
    assert cats(sid, "The work order WO-1187 is now waiting for parts.") == []


def test_corrections_never_instruct_an_action():
    import inspect
    src = inspect.getsource(guard.check_agent_utterance)
    assert "Do NOT perform any" in src and "call {TOOL_HINT" not in src


def test_negated_contractions_and_announced_outages():
    import time
    from app import tunnel
    sid = _session()
    # live false positive: "didn't" was not treated as a negation
    assert cats(sid, "I attempted to retrieve information about the previous shift but it didn't go through.") == []
    # once the system itself announced the outage, the agent repeating it is not a false claim
    tunnel.state["down_announced_at"] = time.time()
    try:
        assert cats(sid, "I can't reach the maintenance system right now.") == []
    finally:
        tunnel.state["down_announced_at"] = 0
