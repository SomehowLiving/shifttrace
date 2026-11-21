"""Claim guard: catches the agent saying something was done (or looked up) without a matching successful
tool call, records it as a red evidence item, and makes the live agent correct itself.

Observed 19 Nov in a live run with an unreachable MCP server: the LLM said "the procurement request has
been submitted successfully" and quoted a manual section that does not exist. Prompts alone did not
prevent it, so this is enforced from outside the model.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import timedelta

from . import services as svc
from .bus import bus
from .db import connect, parse_ts, tx, utcnow

log = logging.getLogger("shifttrace.guard")

# "n't" is matched without a leading word boundary: in "didn't" there is no boundary before the n.
NEGATION = re.compile(r"(\b(not|nothing|unable|couldn|cannot|failed|no longer|before i|shall i|should i|would you like|do you want|want me to|once you|if you)\b|n't\b|n’t\b)", re.I)

# category -> (claim pattern, tools that make it true, window seconds; None = any time in session)
ACTION_CLAIMS = {
    "order_submitted": (re.compile(r"\b(submitted|placed the order|order (is|has been) placed|been ordered|is ordered|on order|sent to the supplier)\b", re.I),
                        {"approve_procurement_request", "console_approve_procurement"}, 120),
    "draft_created": (re.compile(r"\b(drafted|created (a|the) (procurement )?(request|draft)|draft (is )?ready)\b", re.I),
                      {"create_procurement_request", "create_stock_transfer"}, 120),
    "reserved": (re.compile(r"\b(reserved|have reserved|has been reserved)\b", re.I), {"reserve_spare_part"}, 120),
    "wo_updated": (re.compile(r"\b(work order (has been|is now|is|was)( \w+)? (updated|set|moved|changed|put on hold)|(updated|set) the work order|on hold for parts|now waiting (for )?parts)\b", re.I),
                   {"update_work_order"}, 120),
    "escalated": (re.compile(r"\b(escalated|raised an escalation)\b", re.I), {"escalate_incident"}, 120),
    "recorded": (re.compile(r"\b(i('ve| have) (recorded|logged|noted)|has been (recorded|logged)|added (it )?to the (timeline|record))\b", re.I),
                 {"record_observation", "record_reading", "update_open_item"}, 120),
    "handoff": (re.compile(r"\bhandoff (is )?(ready|created|saved|stored|done)|(created|prepared|generated) the (shift )?handoff\b", re.I),
                {"create_shift_handoff"}, 180),
    "transferred": (re.compile(r"\b(stock (has been|was|is) moved|(has been|have been|was|were) (moved|transferred)|transfer (is|has been) (done|complete|completed|confirmed)|posted (it )?to the erp|erp (has been|is) updated)\b", re.I),
                    {"confirm_stock_transfer", "console_confirm_transfer"}, 120),
    "follow_up": (re.compile(r"\b(follow[- ]?up (is|has been) (scheduled|created|booked|set)|(i('ve| have)|i) scheduled (a|the) follow[- ]?up|scheduled (it )?for (tomorrow|the next shift))\b", re.I),
                  {"schedule_follow_up"}, 120),
    "learning_record": (re.compile(r"\b(learning record (is|has been|was) (updated|saved|recorded)|recorded (it |that )?as (passed|needs review)|you (have )?passed the module)\b", re.I),
                        {"finish_training_module"}, 180),
}
SOURCE_CLAIMS = {
    "manual": (re.compile(r"\b(the manual|section \d+(\.\d+)?|service manual)\b", re.I),
               {"search_maintenance_manual", "record_reading"}),  # record_reading cites the section its configured limit comes from
    "inventory": (re.compile(r"\b(in stock|out of stock|stores (show|have|has)|inventory (shows|says|tool))\b", re.I), {"check_inventory"}),
    "shipment": (re.compile(r"\b(tracking (shows|says)|carrier (record|tracking) (shows|says)|last scan (was|is|shows))\b", re.I), {"track_shipment"}),
    "history": (re.compile(r"\b(previous (shift|technician)|last shift|yesterday's|the record shows|history shows|handoff (says|shows))\b", re.I),
                {"get_previous_handoff", "get_asset_history", "get_open_work_orders", "get_open_items"}),
}

# A read of the records in this session can legitimately support a *description* of state
# ("WO-1187 is waiting for parts", "the bearing was ordered") -- e.g. the next shift reading the handoff.
RECORD_READS = {"get_previous_handoff", "get_asset_history", "get_open_work_orders"}
# Claiming an outage is also a claim: it must be backed by an actual tool failure.
OUTAGE = re.compile(r"\b(can(no|')t|cannot|unable to) (reach|access|connect to) the (maintenance|inventory) system\b", re.I)

_flagged: set[tuple[str, str, str]] = set()


def forget(session_id: str | None = None) -> None:
    """Session IDs restart at S-1001 after a data reset, so per-session dedupe keys must be dropped when a
    session ID is (re)issued; otherwise a reused ID silently skips claim checks (observed in the 21 Nov run)."""
    for key in [k for k in _flagged if session_id is None or k[0] == session_id]:
        _flagged.discard(key)
TOOL_HINT = {
    "order_submitted": "approve_procurement_request", "draft_created": "create_procurement_request", "reserved": "reserve_spare_part",
    "wo_updated": "update_work_order", "escalated": "escalate_incident", "recorded": "record_observation", "handoff": "create_shift_handoff",
    "manual": "search_maintenance_manual", "inventory": "check_inventory", "history": "get_previous_handoff", "false_outage": "any tool",
    "transferred": "confirm_stock_transfer", "follow_up": "schedule_follow_up", "learning_record": "finish_training_module", "shipment": "track_shipment",
}


INVITATION = re.compile(r"\b(ask me|you can ask|point your camera|let me know|tell me|feel free)\b", re.I)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def find_violations(session_id: str, text: str) -> list[tuple[str, str]]:
    """Return [(category, sentence)] for claims without a supporting successful tool call."""
    conn = connect()
    try:
        rows = conn.execute("SELECT tool_name, status, ts FROM tool_actions WHERE session_id=? AND status='ok'", (session_id,)).fetchall()
    finally:
        conn.close()
    now = parse_ts(utcnow())
    ok_any = {r["tool_name"] for r in rows}
    out: list[tuple[str, str]] = []
    for sent in _sentences(text):
        if OUTAGE.search(sent):
            conn = connect()
            try:
                failed = conn.execute("SELECT 1 FROM tool_actions WHERE session_id=? AND status='error' AND ts>=?",
                                      (session_id, (now - timedelta(seconds=90)).isoformat().replace("+00:00", "Z"))).fetchone()
            finally:
                conn.close()
            from . import tunnel  # the system itself may have told the agent tools are down
            announced = time.time() - float(tunnel.state.get("down_announced_at") or 0) < 120 or tunnel.state.get("healthy") is False
            if not failed and not announced:
                out.append(("false_outage", sent))
            continue
        if NEGATION.search(sent) or INVITATION.search(sent) or sent.rstrip().endswith("?"):
            continue
        for cat, (pat, tools, window) in ACTION_CLAIMS.items():
            if pat.search(sent):
                recent = {r["tool_name"] for r in rows if now - parse_ts(r["ts"]) <= timedelta(seconds=window)}
                if not (recent & tools) and not (ok_any & RECORD_READS and cat in ("order_submitted", "wo_updated", "reserved", "escalated")):
                    out.append((cat, sent))
        for cat, (pat, tools) in SOURCE_CLAIMS.items():
            if pat.search(sent) and not (ok_any & tools):
                out.append((cat, sent))
    return out


async def check_agent_utterance(session_id: str, turn_id: str, text: str) -> list[dict]:
    from .agora_session import agora_sessions  # local import: avoid cycle

    flagged = []
    conn = connect()
    try:  # the greeting (spoken before the technician says anything) is not a claim
        spoke = conn.execute("SELECT 1 FROM transcript_events WHERE session_id=? AND role='user' LIMIT 1", (session_id,)).fetchone()
    finally:
        conn.close()
    if not spoke:
        return flagged
    for cat, sent in find_violations(session_id, text):
        key = (session_id, turn_id, cat)
        if key in _flagged:
            continue
        _flagged.add(key)
        with tx() as conn:
            s = conn.execute("SELECT asset_id FROM sessions WHERE session_id=?", (session_id,)).fetchone()
            ev = svc.record_evidence(
                conn, session_id=session_id, asset_id=s["asset_id"] if s else svc.fallback_asset_id(conn), event_type="system_record",
                source_type="claim_guard", status="error",
                title=f"Unverified agent claim ({cat.replace('_', ' ')}): no successful {TOOL_HINT[cat]} call",
                detail=f"Agent said: \"{sent}\"", payload={"category": cat, "turn_id": turn_id})
        bus.publish("evidence", {"id": ev["id"]})
        bus.publish("claim", {"session_id": session_id, "category": cat})
        log.warning("unverified claim session=%s cat=%s: %s", session_id, cat, sent)
        if cat == "false_outage":
            correction = ("SYSTEM CHECK: you said the maintenance system is unreachable, but no tool call failed. The tools are available. "
                          "Apologise briefly and use the tools to do what the technician asked; do not take any action they did not ask for.")
        else:
            correction = (f"SYSTEM CHECK FAILED. You just said: \"{sent}\". No successful {TOOL_HINT[cat]} call supports it, so it is NOT true. "
                          "Tell the technician in one sentence that you were wrong and it was not done or not checked. Do NOT perform any "
                          "action now; ask the technician whether they want it done.")
        await agora_sessions.think(session_id, correction)
        flagged.append({"category": cat, "sentence": sent, "event_id": ev["id"]})
    return flagged
