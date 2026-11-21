"""Tool implementations shared by the MCP server (called by Agora cloud) and the console API.

Each tool:
  * runs in its own transaction,
  * is written to the tool_actions audit log with input, result, status and latency,
  * re-reads mutated records on a fresh connection and reports `verified`,
  * publishes a bus event so the console updates live.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable

from . import media, packs, services as svc
from . import integrations
from . import workplace as wp
from .bus import bus
from .config import settings
from .db import connect, row_to_dict, tx, utcnow
from .services import ServiceError, SessionContext

MUTATING = {"create_stock_transfer", "confirm_stock_transfer", "schedule_follow_up", "record_training_answer", "finish_training_module",
            "reserve_spare_part", "create_procurement_request", "approve_procurement_request", "update_work_order",
            "escalate_incident", "record_observation", "record_reading", "update_open_item", "create_shift_handoff"}


def _ctx(session_id: str | None) -> SessionContext:
    conn = connect()
    try:
        return SessionContext.resolve(conn, session_id)
    finally:
        conn.close()


async def run_tool(name: str, args: dict[str, Any], session_id: str | None, caller: str,
                   impl: Callable[[SessionContext], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
    ctx = _ctx(session_id)
    started = time.perf_counter()
    try:
        _check_task_allows(name, ctx, caller)
        result = await impl(ctx)
        status = result.pop("_status", "ok")
    except ServiceError as e:
        result, status = e.to_dict(), "error"
    except Exception as e:  # unexpected: still report honestly
        result, status = {"ok": False, "error": "internal_error", "message": f"{type(e).__name__}: {e}"}, "error"
    ms = int((time.perf_counter() - started) * 1000)
    with tx() as conn:
        action_id = svc.log_tool_action(conn, ctx.session_id, name, caller, args, result, status, ms)
    bus.publish("tool", {"id": action_id, "tool": name, "status": status, "session_id": ctx.session_id, "caller": caller})
    if name in MUTATING and status == "ok":
        bus.publish("state", {"tool": name})
    if status == "ok" and isinstance(result, dict) and result.get("verified") is True:
        # Verified business actions go out to the site's connected systems (Slack, Teams, Jira, webhooks...).
        integrations.emit(integrations.event_for(name, args, result, ctx.session_id, ctx.asset_id))
    return result


def _check_task_allows(name: str, ctx: SessionContext, caller: str) -> None:
    """Server-side half of the per-task tool allowlist (Agora's allowed_tools is the other half): an agent in,
    say, a read-only briefing session cannot reach a write tool even if the model tries."""
    if caller != "agora_mcp" or not ctx.task_id:
        return
    try:
        task = packs.get_task(ctx.task_id)
    except packs.PackError:
        return
    allowed = packs.allowed_tools(task)  # the task's list, or the core tools (domain tools are opt-in)
    if name not in allowed:
        raise ServiceError("not_available_in_task",
                           f"{name} is not available in a {task['label']} session. Nothing was changed.",
                           task=task["id"], allowed_tools=allowed)


def _verify(sql: str, params: tuple, check: Callable[[dict[str, Any]], bool]) -> tuple[bool, dict[str, Any] | None]:
    conn = connect()  # fresh connection: proves the write was committed
    try:
        row = row_to_dict(conn.execute(sql, params).fetchone())
    finally:
        conn.close()
    return (row is not None and check(row)), row


# ----------------------------------------------------------------------------- reads

async def get_asset_history(ctx: SessionContext, asset_id: str | None) -> dict[str, Any]:
    with tx() as conn:
        h = svc.asset_history(conn, asset_id or ctx.asset_id, limit_events=25)
    a = h["asset"]
    return {
        "ok": True,
        "asset": {k: a[k] for k in ("asset_id", "name", "model", "location", "status", "criticality")},
        "work_orders": [
            {"work_order_id": w["work_order_id"], "title": w["title"], "status": w["status"], "priority": w["priority"],
             "log": [f"{l['ts'][:16]} {l['author']}: {l['note']}" for l in w["log"]][-4:]}
            for w in h["work_orders"]
        ],
        "sessions": [{k: s[k] for k in ("session_id", "technician", "shift_label", "started_at", "summary")} for s in h["sessions"][:5]],
        "evidence": [
            {"event_id": e["id"], "ts": e["ts"][:16], "type": e["event_type"], "source": e["source_type"], "text": e["title"],
             "status": e["status"]}
            for e in h["evidence"]
        ],
        "note": "Each evidence item has a source: camera_model = model reading of a camera frame (not a diagnosis); technician = what a person said; cmms/tool_result = system record; agent_inference = hypothesis.",
    }


async def get_open_work_orders(ctx: SessionContext, asset_id: str | None) -> dict[str, Any]:
    with tx() as conn:
        wos = svc.open_work_orders(conn, asset_id or ctx.asset_id)
    return {"ok": True, "work_orders": [
        {"work_order_id": w["work_order_id"], "title": w["title"], "status": w["status"], "priority": w["priority"],
         "assigned_to": w["assigned_to"], "description": w["description"],
         "log": [f"{l['ts'][:16]} {l['author']}: {l['note']}" for l in w["log"]][-5:]}
        for w in wos]}


async def get_previous_handoff(ctx: SessionContext, asset_id: str | None) -> dict[str, Any]:
    with tx() as conn:
        h = svc.latest_handoff(conn, asset_id or ctx.asset_id, exclude_session=ctx.session_id)
    if not h:
        return {"ok": True, "handoff": None, "message": "No previous handoff exists for this asset."}
    r = h["report"]
    return {
        "ok": True,
        "handoff_id": h["handoff_id"],
        "created_at": h["created_at"],
        "created_by": h["created_by"],
        "headline": r.get("headline"),
        "spoken_summary": r.get("spoken_summary"),
        "work_order": r.get("work_order"),
        "observations": [{"text": o.get("text"), "source": o.get("source")} for o in r.get("observations", [])][:8],
        "actions_completed": [a.get("text") for a in r.get("actions_completed", [])][:8],
        "actions_failed_or_pending": [a.get("text") for a in r.get("actions_failed_or_pending", [])][:6],
        "parts": r.get("parts", []),
        "ruled_out": [x.get("text") for x in r.get("ruled_out", [])],
        "open_loops": [x.get("text") for x in r.get("open_loops", [])],
        "suggested_next_steps": r.get("suggested_next_steps", []),
    }


async def get_open_items(ctx: SessionContext, asset_id: str | None) -> dict[str, Any]:
    with tx() as conn:
        items = svc.open_items(conn, asset_id or ctx.asset_id)
    return {"ok": True, "open_items": [
        {"event_id": i["id"], "type": i["event_type"], "text": i["title"], "detail": i["detail"], "raised": i["ts"][:16],
         "raised_by": i.get("raised_by_technician")} for i in items]}


async def search_maintenance_manual(ctx: SessionContext, query: str, asset_id: str | None) -> dict[str, Any]:
    with tx() as conn:
        asset = svc.get_asset(conn, asset_id or ctx.asset_id)
        hits = svc.search_manual(conn, asset["model"], query, k=3)
    if not hits:
        return {"ok": True, "sections": [], "message": f"No section of the {asset['model']} manual matches that query."}
    return {"ok": True, "manual": f"{asset['model']} service manual (fictional demo manual)", "sections": hits}


async def check_inventory(ctx: SessionContext, part: str) -> dict[str, Any]:
    with tx() as conn:
        asset = svc.get_asset(conn, ctx.asset_id)
        matches = svc.check_inventory(conn, part, asset["model"])
    return {"ok": True, "query": part, "matches": matches,
            "summary": "; ".join(f"{m['part_id']} {m['name']}: {m['available']} available" for m in matches)}


# ----------------------------------------------------------------------------- writes

async def reserve_spare_part(ctx: SessionContext, part: str, quantity: int, work_order_id: str | None) -> dict[str, Any]:
    with tx() as conn:
        res = svc.reserve_part(conn, ctx, part, quantity, work_order_id)
        r = res["reservation"]
        if not res["duplicate"]:
            svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="action", source_type="tool_result",
                                title=f"Reserved {r['quantity']} x {r['part_id']} ({r['reservation_id']})", payload=r)
    ok, row = _verify("SELECT * FROM reservations WHERE reservation_id=?", (r["reservation_id"],), lambda x: x["status"] == "ACTIVE")
    return {"ok": ok, "verified": ok, "duplicate": res["duplicate"], "reservation": row}


async def create_procurement_request(ctx: SessionContext, part: str, quantity: int, work_order_id: str | None, reason: str | None) -> dict[str, Any]:
    with tx() as conn:
        res = svc.create_procurement(conn, ctx, part, quantity, work_order_id, reason)
        pr = res["request"]
        if not res["duplicate"]:
            svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="action", source_type="tool_result",
                                title=f"Procurement draft {pr['request_id']} created: {pr['quantity']} x {pr['part_id']} (awaiting approval)", payload=pr)
    ok, row = _verify("SELECT * FROM procurement_requests WHERE request_id=?", (pr["request_id"],), lambda x: x["status"] in ("PENDING_APPROVAL", "SUBMITTED"))
    bus.publish("approval", {"request_id": pr["request_id"], "status": row["status"] if row else None})
    status = row["status"] if row else "UNKNOWN"
    return {
        "ok": ok, "verified": ok, "duplicate": res["duplicate"], "request_id": pr["request_id"], "status": status,
        "request": {k: pr[k] for k in ("request_id", "part_id", "part_name", "quantity", "work_order_id", "supplier", "lead_time_days")},
        "note": res.get("note"),
        "next": ("Already submitted earlier; do not submit again." if status == "SUBMITTED" else
                 "NOT submitted yet. Read the draft back (part, quantity, work order) and ask the technician to confirm. "
                 "Only after they say yes, call approve_procurement_request."),
    }


async def approve_procurement_request(ctx: SessionContext, request_id: str) -> dict[str, Any]:
    with tx() as conn:
        try:
            pr = svc.get_procurement(conn, request_id)
        except ServiceError:
            # Observed live: the LLM passed the asset ID as the request ID. If this session has exactly one
            # pending draft, that is the one being discussed; the spoken-yes gate below still applies.
            pending = conn.execute("SELECT request_id FROM procurement_requests WHERE session_id=? AND status='PENDING_APPROVAL'",
                                   (ctx.session_id,)).fetchall()
            if len(pending) != 1:
                raise
            pr = svc.get_procurement(conn, pending[0]["request_id"])
    if pr["status"] == "SUBMITTED":
        return {"ok": True, "verified": True, "duplicate": True, "request_id": pr["request_id"], "status": "SUBMITTED",
                "expected_by": pr["expected_by"], "message": "Already submitted; no duplicate order was placed."}
    if pr["status"] != "PENDING_APPROVAL":
        raise ServiceError("invalid_state", f"{pr['request_id']} is {pr['status']}; it cannot be submitted.")
    deadline = time.monotonic() + settings.approval_wait_s
    approval = None
    while True:
        conn = connect()
        try:
            approval = svc.find_spoken_approval(conn, ctx.session_id, int(pr["transcript_watermark"]))
            fresh = svc.get_procurement(conn, pr["request_id"])
        finally:
            conn.close()
        if fresh["status"] != "PENDING_APPROVAL":  # decided in the console meanwhile
            return {"ok": fresh["status"] == "SUBMITTED", "verified": True, "request_id": fresh["request_id"], "status": fresh["status"],
                    "expected_by": fresh["expected_by"], "message": f"Decided in the console: {fresh['status']}."}
        if approval or time.monotonic() >= deadline:
            break
        await asyncio.sleep(0.4)
    if not approval:
        return {"_status": "approval_required", "ok": False, "status": "APPROVAL_REQUIRED", "request_id": pr["request_id"],
                "message": "Not submitted. No spoken confirmation from the technician was heard after the draft was created. "
                           "Ask them to confirm out loud, or to press Approve in the console."}
    with tx() as conn:
        res = svc.submit_procurement(conn, pr["request_id"], ctx.technician, "voice", f"\"{approval['text']}\" (transcript #{approval['id']})")
        out = res["request"]
        svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="action", source_type="tool_result",
                            title=(f"{out['request_id']} submitted to supplier, expected by {out['expected_by']}" if out["status"] == "SUBMITTED"
                                   else f"{out['request_id']} {out['status']}: {out['failure_reason']}"),
                            detail=f"Approved by voice: \"{approval['text']}\"", payload=out, verified_by=ctx.technician)
    ok, row = _verify("SELECT * FROM procurement_requests WHERE request_id=?", (pr["request_id"],), lambda x: x["status"] == "SUBMITTED")
    bus.publish("approval", {"request_id": pr["request_id"], "status": row["status"] if row else None})
    if not ok:
        return {"_status": "error", "ok": False, "verified": False, "request_id": pr["request_id"], "status": row["status"] if row else "UNKNOWN",
                "message": f"The order was NOT placed: {row['failure_reason'] if row else 'record missing'}"}
    return {"ok": True, "verified": True, "request_id": row["request_id"], "status": row["status"], "supplier": row["supplier"],
            "supplier_ref": row["supplier_ref"], "expected_by": row["expected_by"], "approved_via": "voice",
            "approval_evidence": row["approval_evidence"]}


async def update_work_order(ctx: SessionContext, work_order_id: str | None, status: str | None, note: str, via: str = "voice") -> dict[str, Any]:
    with tx() as conn:
        wo_id = work_order_id or svc._default_work_order(conn, ctx.asset_id)
        if not wo_id:
            raise ServiceError("no_open_work_order", "There is no open work order for this asset.")
        wo = svc.update_work_order(conn, ctx, wo_id, status, note, via=via)
        last = wo["log"][-1]
        svc.record_evidence(conn, session_id=ctx.session_id, asset_id=wo["asset_id"], event_type="action", source_type="tool_result",
                            title=f"{wo['work_order_id']} {last['status_from']} -> {last['status_to']}", detail=note, payload={"log_id": last["id"]})
    expected = wo["status"]
    ok, row = _verify("SELECT * FROM work_orders WHERE work_order_id=?", (wo["work_order_id"],), lambda x: x["status"] == expected)
    return {"ok": ok, "verified": ok, "work_order_id": wo["work_order_id"], "status": row["status"] if row else None,
            "updated_at": row["updated_at"] if row else None, "note_logged": note}


async def escalate_incident(ctx: SessionContext, work_order_id: str | None, severity: str, reason: str) -> dict[str, Any]:
    with tx() as conn:
        res = svc.escalate(conn, ctx, work_order_id, severity, reason)
        e = res["escalation"]
        if not res["duplicate"]:
            svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="action", source_type="tool_result",
                                title=f"Escalation {e['escalation_id']} ({e['severity']}) raised", detail=reason, payload=e)
    ok, row = _verify("SELECT * FROM escalations WHERE escalation_id=?", (e["escalation_id"],), lambda x: x["status"] == "OPEN")
    return {"ok": ok, "verified": ok, "duplicate": res["duplicate"], "escalation": row,
            "message": _escalation_message()}


def _escalation_message() -> str:
    targets = integrations.enabled_targets("escalation.raised")
    if targets:
        return ("Recorded in SHIFTTRACE and queued for delivery to: " + ", ".join(targets) +
                ". Say it has been sent to them; do not say anyone has read it or replied.")
    return "Recorded in SHIFTTRACE and visible to the supervisor queue. No external system is connected, so nobody was paged."


async def record_observation(ctx: SessionContext, kind: str, summary: str, detail: str | None) -> dict[str, Any]:
    k = kind.strip().lower().replace(" ", "_")
    if k not in svc.EVENT_KINDS:
        raise ServiceError("bad_kind", f"kind must be one of {', '.join(svc.EVENT_KINDS)}.")
    event_type, source, status = svc.EVENT_KINDS[k]
    media_ref = media.latest_snapshot(ctx.session_id, max_age_s=20) if k == "visual" else None
    with tx() as conn:
        ev = svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type=event_type, source_type=source,
                                 title=summary, detail=detail, status=status,
                                 model_id=svc.VISION_MODEL_LABEL if k == "visual" else None, media_ref=media_ref)
    # Re-read on a fresh connection before reporting it stored (same rule as every other write).
    ok, _ = _verify("SELECT * FROM evidence WHERE id=?", (ev["id"],),
                    lambda r: r["title"] == summary and r["session_id"] == ctx.session_id and r["event_type"] == event_type
                    and r["source_type"] == source)
    bus.publish("evidence", {"id": ev["id"]})
    if not ok:
        return {"_status": "error", "ok": False, "verified": False, "event_id": ev["id"],
                "message": "The observation could not be read back from the record, so it may not be stored. Say so; do not claim it was recorded."}
    out: dict[str, Any] = {"ok": True, "verified": True, "event_id": ev["id"], "recorded_as": event_type, "source": source,
                           "snapshot_attached": bool(media_ref)}
    if k in ("visual", "technician_report", "audio"):
        conn = connect()
        try:
            loops = svc.open_items(conn, ctx.asset_id)
        finally:
            conn.close()
        if loops:
            out["open_loops"] = [{"event_id": l["id"], "text": l["title"]} for l in loops]
            out["hint"] = ("If this evidence answers one of these open loops, tell the technician and call update_open_item "
                           "(status answered, confirmed or ruled_out). Do not close a loop on weak evidence.")
    return out


async def record_reading(ctx: SessionContext, reading: str, value: float, unit: str | None, source: str = "technician") -> dict[str, Any]:
    """Record a numeric reading and check it against the machine's configured limits (deterministic)."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ServiceError("bad_value", "value must be a number, for example 262 or 12.4.")
    camera = (source or "").strip().lower() in ("camera", "visual", "display", "panel")
    with tx() as conn:
        asset = svc.get_asset(conn, ctx.asset_id)
        ev_ = svc.evaluate_reading(asset, reading, value, unit)
        label = ev_.get("reading") or reading.strip()
        u = ev_.get("unit") or svc.norm_unit(unit)
        title = f"{label}: {value:g} {u}".strip()
        if ev_["status"] in ("out_of_limit", "outside_normal"):
            title += f" ({ev_['status'].replace('_', ' ')})"
        media_ref = media.latest_snapshot(ctx.session_id, max_age_s=20) if camera else None
        ev = svc.record_evidence(
            conn, session_id=ctx.session_id, asset_id=ctx.asset_id,
            event_type="visual_observation" if camera else "technician_statement",
            source_type="camera_model" if camera else "technician", title=title, detail=ev_["say"],
            status="unverified" if camera else None, model_id=svc.VISION_MODEL_LABEL if camera else None, media_ref=media_ref,
            payload={"reading": label, "value": value, "unit": u, "evaluation": ev_["status"], "limit": ev_.get("limit")})
        follow = None
        if ev_["status"] == "out_of_limit":
            follow = svc.record_evidence(
                conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="open_question", source_type="agent_inference",
                title=f"{label} {value:g} {u} out of limit: follow up", detail=ev_["say"], status="open", related_id=ev["id"])
    ok, row = _verify("SELECT * FROM evidence WHERE id=?", (ev["id"],), lambda r: r["title"] == title)
    bus.publish("evidence", {"id": ev["id"]})
    return {"ok": True, "verified": ok, "event_id": ev["id"], "recorded_as": ev["event_type"], "evaluation": ev_["status"],
            "say": ev_["say"], "follow_up_logged": follow["id"] if follow else None,
            "instruction": "Tell the technician the evaluation in your own words using 'say'. Do not compare the numbers yourself."}


async def update_open_item(ctx: SessionContext, event_id: int, status: str, note: str) -> dict[str, Any]:
    with tx() as conn:
        item = svc.update_open_item(conn, ctx, int(event_id), status, note)
    ok, row = _verify("SELECT * FROM evidence WHERE id=?", (item["id"],), lambda r: r["status"] == item["status"])
    bus.publish("evidence", {"id": item["id"]})
    if not ok:
        return {"_status": "error", "ok": False, "verified": False, "event_id": item["id"], "status": row["status"] if row else None,
                "message": "The change could not be read back from the record, so the item may still be open. Say so."}
    return {"ok": True, "verified": True, "event_id": item["id"], "text": item["title"], "status": item["status"]}


async def create_shift_handoff(ctx: SessionContext) -> dict[str, Any]:
    if not ctx.session_id:
        raise ServiceError("no_session", "There is no active maintenance session to hand off.")
    with tx() as conn:
        h = svc.compose_handoff(conn, ctx.session_id)
    ok, row = _verify("SELECT * FROM handoffs WHERE handoff_id=?", (h["handoff_id"],), lambda x: x["status"] == "PUBLISHED")
    bus.publish("handoff", {"handoff_id": h["handoff_id"]})
    r = h["report"]
    return {"ok": ok, "verified": ok, "handoff_id": h["handoff_id"], "headline": r["headline"],
            "spoken_summary": r["spoken_summary"], "open_loops": [l["text"] for l in r["open_loops"]],
            "actions_completed": len(r["actions_completed"]), "actions_failed_or_pending": len(r["actions_failed_or_pending"])}


# ----------------------------------------------------------------------------- warehouse and logistics

async def track_shipment(ctx: SessionContext, reference: str | None) -> dict[str, Any]:
    with tx() as conn:
        found = wp.find_shipments(conn, ctx, reference)
    return {"ok": True, "shipments": [
        {"shipment_id": x["shipment_id"], "direction": x["direction"], "status": x["status"], "carrier": x["carrier"],
         "carrier_ref": x["carrier_ref"], "origin": x["origin"], "destination": x["destination"], "eta": x["eta"],
         "items": x["items"], "last_event": x["last_event"], "recent_events": x["events"][:3]} for x in found],
        "say": "Give status, last scan and ETA from these records; say they come from the carrier tracking record."}


async def create_stock_transfer(ctx: SessionContext, part: str, quantity: int, from_location: str, to_location: str,
                                reason: str | None) -> dict[str, Any]:
    with tx() as conn:
        res = wp.create_transfer(conn, ctx, part, quantity, from_location, to_location, reason)
        t = res["transfer"]
        if not res["duplicate"]:
            svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="action", source_type="tool_result",
                                title=f"Stock transfer draft {t['transfer_id']}: {t['quantity']} x {t['part_id']} from {t['from_location']} to {t['to_location']} (awaiting confirmation)",
                                payload=t)
    ok, row = _verify("SELECT * FROM stock_transfers WHERE transfer_id=?", (t["transfer_id"],), lambda x: x["status"] in ("PENDING_CONFIRMATION", "DONE"))
    bus.publish("approval", {"transfer_id": t["transfer_id"], "status": row["status"] if row else None})
    return {"ok": ok, "verified": ok, "duplicate": res["duplicate"], "transfer_id": t["transfer_id"], "status": row["status"] if row else "UNKNOWN",
            "transfer": {k: t[k] for k in ("transfer_id", "part_id", "part_name", "quantity", "from_location", "to_location")},
            "next": ("This draft already exists and is waiting for confirmation. If the worker has just said yes, call confirm_stock_transfer "
                     "now; do not draft it again." if res["duplicate"] else
                     "NOT moved yet. Read it back (item, quantity, from, to) and ask the worker to confirm. Only after they say yes, "
                     "call confirm_stock_transfer.")}


async def confirm_stock_transfer(ctx: SessionContext, transfer_id: str) -> dict[str, Any]:
    with tx() as conn:
        try:
            t = wp.get_transfer(conn, transfer_id)
        except ServiceError:
            pending = conn.execute("SELECT transfer_id FROM stock_transfers WHERE session_id=? AND status='PENDING_CONFIRMATION'", (ctx.session_id,)).fetchall()
            if len(pending) != 1:
                raise
            t = wp.get_transfer(conn, pending[0]["transfer_id"])
    if t["status"] == "DONE":
        return {"ok": True, "verified": True, "duplicate": True, "transfer_id": t["transfer_id"], "status": "DONE", "erp_ref": t["erp_ref"],
                "message": "Already moved; nothing was moved twice."}
    if t["status"] != "PENDING_CONFIRMATION":
        raise ServiceError("invalid_state", f"{t['transfer_id']} is {t['status']}; it cannot be confirmed.")
    deadline = time.monotonic() + settings.approval_wait_s
    while True:  # same spoken-yes gate as procurement: the model cannot confirm its own action
        conn = connect()
        try:
            approval = svc.find_spoken_approval(conn, ctx.session_id, int(t["transcript_watermark"]))
            fresh = wp.get_transfer(conn, t["transfer_id"])
        finally:
            conn.close()
        if fresh["status"] != "PENDING_CONFIRMATION":
            return {"ok": fresh["status"] == "DONE", "verified": True, "transfer_id": fresh["transfer_id"], "status": fresh["status"],
                    "erp_ref": fresh["erp_ref"], "message": f"Decided in the console: {fresh['status']}."}
        if approval or time.monotonic() >= deadline:
            break
        await asyncio.sleep(0.4)
    if not approval:
        return {"_status": "approval_required", "ok": False, "status": "APPROVAL_REQUIRED", "transfer_id": t["transfer_id"],
                "message": "Not moved. No spoken confirmation from the worker was heard after the read-back. Ask them to confirm out loud, or to press Confirm in the console."}
    with tx() as conn:
        quote = f"\"{approval['text']}\" (transcript #{approval['id']})"
        out = wp.confirm_transfer(conn, t["transfer_id"], ctx.technician, "voice", quote)["transfer"]
        svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="action", source_type="tool_result",
                            title=(f"{out['transfer_id']} done: {out['quantity']} x {out['part_id']} moved {out['from_location']} to {out['to_location']}, ERP {out['erp_ref']}"
                                   if out["status"] == "DONE" else f"{out['transfer_id']} {out['status']}: {out['failure_reason']}"),
                            detail=f"Confirmed by voice: {quote}", payload=out, verified_by=ctx.technician)
    return verify_transfer(out["transfer_id"])


def verify_transfer(transfer_id: str) -> dict[str, Any]:
    """Re-read the transfer, both stock rows and the ERP posting on a fresh connection."""
    conn = connect()
    try:
        t = row_to_dict(conn.execute("SELECT * FROM stock_transfers WHERE transfer_id=?", (transfer_id,)).fetchone())
        erp = conn.execute("SELECT * FROM erp_postings WHERE doc_ref=?", (transfer_id,)).fetchone() if t else None
        levels = {r["location"]: r["quantity"] for r in conn.execute("SELECT location, quantity FROM stock_levels WHERE part_id=?", (t["part_id"],)).fetchall()} if t else {}
    finally:
        conn.close()
    bus.publish("approval", {"transfer_id": transfer_id, "status": t["status"] if t else None})
    ok = bool(t and t["status"] == "DONE" and erp is not None)
    if not ok:
        return {"_status": "error", "ok": False, "verified": False, "transfer_id": transfer_id, "status": t["status"] if t else "UNKNOWN",
                "message": f"The stock was NOT moved: {(t or {}).get('failure_reason') or 'record missing'}"}
    return {"ok": True, "verified": True, "transfer_id": transfer_id, "status": "DONE", "erp_ref": t["erp_ref"],
            "stock_now": {t["from_location"]: levels.get(t["from_location"]), t["to_location"]: levels.get(t["to_location"])},
            "confirmed_via": t["confirmation_via"]}


# ----------------------------------------------------------------------------- follow-ups

async def schedule_follow_up(ctx: SessionContext, title: str, due: str | None, assignee: str | None) -> dict[str, Any]:
    with tx() as conn:
        res = wp.create_follow_up(conn, ctx, title, due, assignee)
        f = res["follow_up"]
        if not res["duplicate"]:
            when = f["due_date"] or f["due_text"] or "no date"
            svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="action", source_type="tool_result",
                                title=f"Follow-up {f['follow_up_id']} scheduled: {f['title']} (due {when}, {f['assignee']})", payload=f)
    ok, row = _verify("SELECT * FROM follow_ups WHERE follow_up_id=?", (f["follow_up_id"],), lambda x: x["status"] == "OPEN" and x["title"] == f["title"])
    return {"ok": ok, "verified": ok, "duplicate": res["duplicate"], "follow_up_id": f["follow_up_id"], "title": f["title"],
            "due": f["due_date"] or f["due_text"], "assignee": f["assignee"]}


# ----------------------------------------------------------------------------- training and onboarding

async def get_training_module(ctx: SessionContext, module_id: str | None) -> dict[str, Any]:
    with tx() as conn:
        asset = wp.asset_for(conn, ctx)
        m = wp.get_module(asset, module_id)
        rec = conn.execute("SELECT status, score, attempts, updated_at FROM learning_records WHERE trainee=? AND module_id=?",
                           (ctx.technician, m["module_id"])).fetchone()
    return {"ok": True, "module_id": m["module_id"], "title": m["title"], "pass_score": int(m.get("pass_score", 80)),
            "intro": m.get("intro"), "questions": [{"question_id": q["id"], "ask": q["ask"], "section": q.get("section")} for q in m["questions"]],
            "trainee": ctx.technician, "previous_record": dict(rec) if rec else None,
            "next": "Ask the questions one at a time. After each answer call record_training_answer with the worker's words; never mark an answer yourself."}


async def record_training_answer(ctx: SessionContext, question_id: str, answer: str, module_id: str | None) -> dict[str, Any]:
    with tx() as conn:
        asset = wp.asset_for(conn, ctx)
        m = wp.get_module(asset, module_id)
        r = wp.record_answer(conn, ctx, m, question_id, answer)
        q = r["question"]
        detail = f"Q: {q['ask']}\nA: \"{answer}\"\nMissing: {', '.join(r['missing']) or 'nothing'}"
        svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="technician_statement", source_type="technician",
                            title=f"Training {m['module_id']} {q['id']}: {r['result']}", detail=detail,
                            payload={k: r[k] for k in ("result", "matched", "missing")})
    ok, _ = _verify("SELECT * FROM training_answers WHERE id=?", (r["answer_id"],), lambda x: x["result"] == r["result"])
    return {"ok": ok, "verified": ok, "question_id": q["id"], "result": r["result"], "missing_key_points": r["missing"],
            "section": q.get("section"), "explain": q.get("explain"),
            "say": ("Tell them it is correct and add one line from 'explain'." if r["result"] == "correct" else
                    f"Tell them it is {r['result']}, say what was missing, and give the right answer from 'explain' (manual section {q.get('section')}).")}


async def finish_training_module(ctx: SessionContext, module_id: str | None) -> dict[str, Any]:
    with tx() as conn:
        asset = wp.asset_for(conn, ctx)
        m = wp.get_module(asset, module_id)
        res = wp.finish_module(conn, ctx, m)
        svc.record_evidence(conn, session_id=ctx.session_id, asset_id=ctx.asset_id, event_type="action", source_type="tool_result",
                            title=f"Learning record updated: {ctx.technician}, {m['title']}: {res['score']}%, {res['status'].replace('_', ' ').lower()}",
                            payload={**res, "module_id": m["module_id"]})
    ok, row = _verify("SELECT * FROM learning_records WHERE trainee=? AND module_id=?", (ctx.technician, m["module_id"]),
                      lambda x: x["score"] == res["score"] and x["status"] == res["status"])
    return {"ok": ok, "verified": ok, "module_id": m["module_id"], "title": m["title"], **res,
            "say": ("Say the score and that it is recorded as passed." if res["passed"] else
                    "Say the score, that it is recorded as needs review, which topics to revisit, and offer to schedule a follow-up session.")}


def stamp() -> str:
    return utcnow()
