"""Console REST API + SSE stream (local port only; never tunnelled)."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import capture, guard, media, packs, services as svc, testkit, tools, tunnel
from . import integrations, reports
from . import workplace as wp
from .agora_session import agora_sessions
from .bus import bus
from .config import settings
from .db import connect, next_id, row_to_dict, rows_to_dicts, tx, utcnow
from .seed import reset_database
from .services import ServiceError, SessionContext

log = logging.getLogger("shifttrace.api")
router = APIRouter(prefix="/api")


def _q(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    conn = connect()
    try:
        return rows_to_dicts(conn.execute(sql, params).fetchall())
    finally:
        conn.close()


def _one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    rows = _q(sql, params)
    return rows[0] if rows else None


def _service(fn, *args):
    conn = connect()
    try:
        return fn(conn, *args)
    except ServiceError as e:
        raise HTTPException(status_code=404 if e.code.endswith("not_found") else 400, detail=e.to_dict())
    finally:
        conn.close()


# ----------------------------------------------------------------------------- status

@router.get("/health")
async def health() -> dict[str, Any]:
    conn = connect()
    try:
        assets = conn.execute("SELECT count(*) FROM assets").fetchone()[0]
    finally:
        conn.close()
    return {"ok": True, "db_assets": assets, "time": utcnow(), **settings.readiness(), "packs": packs.selected_pack_ids(),
            "tunnel": tunnel.state, "active_agents": list(agora_sessions._sessions.keys())}


# ----------------------------------------------------------------------------- packs / tasks (configuration)

def _task_view(t: dict[str, Any]) -> dict[str, Any]:
    return {"id": t["id"], "label": t["label"], "summary": t.get("summary", ""), "goal": t["goal"],
            "procedure": t.get("procedure") or [], "restricted_tools": t.get("tools"), "read_only": bool(t.get("read_only"))}


@router.get("/packs")
async def list_packs() -> list[dict[str, Any]]:
    return packs.pack_summaries()


@router.get("/tasks")
async def list_tasks(asset_id: str | None = None) -> dict[str, Any]:
    if asset_id:
        asset = _service(svc.get_asset, asset_id)
        offered = packs.tasks_for_asset(asset)
        return {"asset_id": asset["asset_id"], "default": packs.default_task_id(asset), "tasks": [_task_view(t) for t in offered]}
    return {"asset_id": None, "default": packs.get_task(None)["id"], "tasks": [_task_view(t) for t in packs.all_tasks()]}


# ----------------------------------------------------------------------------- assets / memory

@router.get("/assets")
async def assets() -> list[dict[str, Any]]:
    return _service(svc.list_assets)


@router.get("/assets/{asset_id}")
async def asset_detail(asset_id: str) -> dict[str, Any]:
    h = _service(svc.asset_history, asset_id, 500)
    h["open_items"] = _service(svc.open_items, asset_id)
    h["handoffs"] = _q("SELECT handoff_id, session_id, created_at, created_by, status FROM handoffs WHERE asset_id=? ORDER BY created_at DESC",
                       (h["asset"]["asset_id"],))
    h["manual_sections"] = _q("SELECT chunk_id, section, title FROM manual_chunks WHERE asset_model=? ORDER BY section", (h["asset"]["model"],))
    return h


@router.get("/manual/{chunk_id}")
async def manual_chunk(chunk_id: str) -> dict[str, Any]:
    row = _one("SELECT * FROM manual_chunks WHERE chunk_id=?", (chunk_id,))
    if not row:
        raise HTTPException(404, "not found")
    return row


@router.get("/manual-search")
async def manual_search(model: str, q: str) -> list[dict[str, Any]]:
    return _service(svc.search_manual, model, q)


# ----------------------------------------------------------------------------- actions centre

@router.get("/inventory")
async def inventory() -> list[dict[str, Any]]:
    conn = connect()
    try:
        return [svc._part_view(conn, p) for p in svc._part_rows(conn)]
    finally:
        conn.close()


@router.get("/procurement")
async def procurement() -> list[dict[str, Any]]:
    return _q("SELECT pr.*, p.name AS part_name FROM procurement_requests pr JOIN parts p ON p.part_id=pr.part_id ORDER BY created_at DESC")


@router.get("/reservations")
async def reservations() -> list[dict[str, Any]]:
    return _q("SELECT r.*, p.name AS part_name FROM reservations r JOIN parts p ON p.part_id=r.part_id ORDER BY created_at DESC")


@router.get("/escalations")
async def escalations() -> list[dict[str, Any]]:
    return _q("SELECT * FROM escalations ORDER BY created_at DESC")


@router.get("/work-orders")
async def work_orders() -> list[dict[str, Any]]:
    rows = _q("SELECT work_order_id FROM work_orders ORDER BY updated_at DESC")
    return [_service(svc.work_order_with_log, r["work_order_id"]) for r in rows]


@router.get("/tool-actions")
async def tool_actions(session_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    if session_id:
        return _q("SELECT * FROM tool_actions WHERE session_id=? ORDER BY id DESC LIMIT ?", (session_id, limit))
    return _q("SELECT * FROM tool_actions ORDER BY id DESC LIMIT ?", (limit,))


class Decision(BaseModel):
    session_id: str | None = None
    by: str | None = None


@router.post("/procurement/{request_id}/approve")
async def approve_from_console(request_id: str, body: Decision) -> dict[str, Any]:
    """Human approval from the console. Submits, verifies, then tells the live agent."""
    pr = _service(svc.get_procurement, request_id)
    sid = body.session_id or pr["session_id"]
    ctx = _ctx(sid)
    approver = body.by or ctx.technician

    async def impl(c: SessionContext) -> dict[str, Any]:
        with tx() as conn:
            res = svc.submit_procurement(conn, request_id, approver, "console", "Approve button in SHIFTTRACE console")
            out = res["request"]
            if not res["duplicate"]:
                svc.record_evidence(conn, session_id=sid, asset_id=c.asset_id, event_type="action", source_type="tool_result",
                                    title=(f"{out['request_id']} submitted to supplier, expected by {out['expected_by']}" if out["status"] == "SUBMITTED"
                                           else f"{out['request_id']} {out['status']}: {out['failure_reason']}"),
                                    detail="Approved in console", payload=out, verified_by=approver)
        verified = _one("SELECT * FROM procurement_requests WHERE request_id=?", (out["request_id"],))
        ok = bool(verified and verified["status"] == "SUBMITTED")
        return {"_status": "ok" if ok else "error", "ok": ok, "verified": ok, "request": verified}

    result = await tools.run_tool("console_approve_procurement", {"request_id": request_id}, sid, "console", impl)
    bus.publish("approval", {"request_id": request_id})
    bus.publish("state", {"tool": "console_approve_procurement"})
    if sid and agora_sessions.is_running(sid):
        r = result.get("request") or {}
        if result.get("ok"):
            msg = (f"The technician approved {r.get('request_id')} in the console. It is verified as submitted to {r.get('supplier')}, "
                   f"supplier reference {r.get('supplier_ref')}, expected by {r.get('expected_by')}. Tell them briefly and offer to update the work order.")
        else:
            msg = (f"The technician approved {request_id} in the console but the order was NOT placed: {r.get('failure_reason')}. "
                   "Tell them plainly and suggest escalating.")
        asyncio.create_task(agora_sessions.think(sid, msg))
    return result


@router.post("/procurement/{request_id}/reject")
async def reject_from_console(request_id: str, body: Decision) -> dict[str, Any]:
    pr = _service(svc.get_procurement, request_id)
    sid = body.session_id or pr["session_id"]
    ctx = _ctx(sid)

    async def impl(c: SessionContext) -> dict[str, Any]:
        with tx() as conn:
            out = svc.reject_procurement(conn, request_id, body.by or ctx.technician, "console")
        return {"ok": True, "request": out}

    result = await tools.run_tool("console_reject_procurement", {"request_id": request_id}, sid, "console", impl)
    bus.publish("approval", {"request_id": request_id})
    if sid and agora_sessions.is_running(sid):
        asyncio.create_task(agora_sessions.think(sid, f"The technician declined {request_id} in the console. Nothing was ordered. Acknowledge briefly."))
    return result


@router.post("/transfers/{transfer_id}/confirm")
async def confirm_transfer_from_console(transfer_id: str, body: Decision) -> dict[str, Any]:
    """Human confirmation from the console: moves the stock, posts to the ERP, re-reads, tells the live agent."""
    t = _service(wp.get_transfer, transfer_id)
    sid = body.session_id or t["session_id"]
    who = body.by or _ctx(sid).technician

    async def impl(c: SessionContext) -> dict[str, Any]:
        with tx() as conn:
            res = wp.confirm_transfer(conn, t["transfer_id"], who, "console", "Confirm button in SHIFTTRACE console")
            out = res["transfer"]
            if not res["duplicate"]:
                svc.record_evidence(conn, session_id=sid, asset_id=c.asset_id, event_type="action", source_type="tool_result",
                                    title=(f"{out['transfer_id']} done: {out['quantity']} x {out['part_id']} moved {out['from_location']} to {out['to_location']}, ERP {out['erp_ref']}"
                                           if out["status"] == "DONE" else f"{out['transfer_id']} {out['status']}: {out['failure_reason']}"),
                                    detail="Confirmed in console", payload=out, verified_by=who)
        return tools.verify_transfer(t["transfer_id"])

    result = await tools.run_tool("console_confirm_transfer", {"transfer_id": t["transfer_id"]}, sid, "console", impl)
    bus.publish("state", {"tool": "console_confirm_transfer"})
    if sid and agora_sessions.is_running(sid):
        msg = (f"The worker confirmed {t['transfer_id']} in the console. It is verified as done and posted to the ERP as {result.get('erp_ref')}. Tell them briefly."
               if result.get("ok") else f"The worker confirmed {t['transfer_id']} in the console but it was NOT done: {result.get('message')}. Tell them plainly.")
        asyncio.create_task(agora_sessions.think(sid, msg))
    return result


@router.post("/transfers/{transfer_id}/cancel")
async def cancel_transfer_from_console(transfer_id: str, body: Decision) -> dict[str, Any]:
    t = _service(wp.get_transfer, transfer_id)
    sid = body.session_id or t["session_id"]

    async def impl(c: SessionContext) -> dict[str, Any]:
        with tx() as conn:
            out = wp.cancel_transfer(conn, t["transfer_id"], body.by or c.technician, "console")
        return {"ok": True, "transfer": out}

    result = await tools.run_tool("console_cancel_transfer", {"transfer_id": t["transfer_id"]}, sid, "console", impl)
    bus.publish("approval", {"transfer_id": t["transfer_id"]})
    if sid and agora_sessions.is_running(sid):
        asyncio.create_task(agora_sessions.think(sid, f"The worker cancelled {t['transfer_id']} in the console. Nothing was moved. Acknowledge briefly."))
    return result


@router.get("/transfers")
async def transfers() -> list[dict[str, Any]]:
    return _q("SELECT t.*, p.name AS part_name FROM stock_transfers t JOIN parts p ON p.part_id=t.part_id ORDER BY t.created_at DESC")


@router.get("/shipments")
async def shipments() -> list[dict[str, Any]]:
    return _q("SELECT * FROM shipments ORDER BY updated_at DESC")  # items_json is decoded to "items" by row_to_dict


@router.get("/follow-ups")
async def follow_ups() -> list[dict[str, Any]]:
    from . import reports
    rows = _q("SELECT * FROM follow_ups ORDER BY created_at DESC")
    for f in rows:  # 'add to calendar' links that need no account connection
        f["calendar"] = reports.calendar_links(f["title"], f["due_date"], f"{f['assignee'] or ''} · {f['asset_id'] or ''} · Shifttrace {f['follow_up_id']}")
    return rows


@router.get("/learning-records")
async def learning_records() -> list[dict[str, Any]]:
    return _q("SELECT * FROM learning_records ORDER BY updated_at DESC")


@router.get("/erp-postings")
async def erp_postings() -> list[dict[str, Any]]:
    return _q("SELECT * FROM erp_postings ORDER BY ts DESC")


# ----------------------------------------------------------------------------- agent quality (improvement loop)

@router.get("/quality")
async def quality_summary() -> dict[str, Any]:
    from . import quality
    return quality.summary()


@router.get("/quality/media/{name}")
async def quality_media(name: str):
    """Thumbnails for the dataset page: only files listed in the media manifest or the generated folder."""
    from . import quality
    m = quality._media()
    allowed = {s["file"] for s in m["sources"]} | set(m["generated"])
    if name not in allowed or "/" in name or "\\" in name:
        raise HTTPException(404, "not in the dataset")
    for d in (quality.EXP / "media" / "web", quality.EXP / "media" / "generated"):
        p = d / name
        if p.is_file():
            return FileResponse(p, media_type=testkit.TYPES.get(p.suffix.lower(), "application/octet-stream") if p.suffix.lower() != ".mp3" else "audio/mpeg")
    raise HTTPException(404, "not found")


# ----------------------------------------------------------------------------- running cost and cost controls

@router.get("/costs")
async def cost_overview() -> dict[str, Any]:
    from . import costs
    sessions = _q("SELECT session_id, asset_id, technician, started_at, status FROM sessions WHERE session_id IN (SELECT DISTINCT session_id FROM usage_segments) ORDER BY started_at DESC LIMIT 20")
    for s in sessions:
        s["cost"] = costs.estimate(s["session_id"])
    return {"projection": costs.projection(), "sessions": sessions}


@router.get("/sessions/{session_id}/cost")
async def session_cost(session_id: str) -> dict[str, Any]:
    from . import costs
    return costs.estimate(session_id)


@router.get("/site-settings")
async def site_settings_get() -> dict[str, Any]:
    from . import costs
    return costs.settings_get()


@router.post("/site-settings")
async def site_settings_set(body: dict[str, Any]) -> dict[str, Any]:
    from . import costs
    out = costs.settings_set(body)
    bus.publish("flags", {"site_settings": True})
    return out


class CameraState(BaseModel):
    on: bool


@router.post("/sessions/{session_id}/camera")
async def camera_state(session_id: str, body: CameraState) -> dict[str, Any]:
    """The browser reports when the camera is publishing, so video minutes (billed higher than audio) are counted."""
    from . import costs
    if body.on and agora_sessions.is_running(session_id):
        costs.segment_start(session_id, "camera")
    else:
        costs.segment_end(session_id, "camera")
    return {"ok": True}


class PauseIn(BaseModel):
    reason: str = "idle"
    idle_min: float | None = None


@router.post("/sessions/{session_id}/voice/pause")
async def pause_voice(session_id: str, body: PauseIn) -> dict[str, Any]:
    """Stop the Agora agent while the session stays open: no agent, ASR, LLM or TTS cost until the worker resumes."""
    s = _one("SELECT * FROM sessions WHERE session_id=?", (session_id,))
    if not s or s["status"] != "ACTIVE":
        raise HTTPException(400, "session is not active")
    stopped = await agora_sessions.stop(session_id)
    why = f"after {body.idle_min:g} min of silence" if body.reason == "idle" and body.idle_min else "by the worker"
    with tx() as conn:
        ev = svc.record_evidence(conn, session_id=session_id, asset_id=s["asset_id"], event_type="system_record", source_type="cmms",
                                 title=f"Voice agent paused {why}; no Agora, LLM or voice cost until resumed")
    bus.publish("evidence", {"id": ev["id"]})
    bus.publish("voice", {"session_id": session_id, "status": "PAUSED"})
    return {"ok": True, "agent_stopped": stopped}


# ----------------------------------------------------------------------------- integrations (connected systems)

@router.get("/integrations")
async def integrations_status() -> dict[str, Any]:
    events = _q("SELECT * FROM integration_events ORDER BY id DESC LIMIT 60")
    deliveries = _q("SELECT * FROM integration_deliveries ORDER BY id DESC LIMIT 300")
    by_event: dict[int, list[dict[str, Any]]] = {}
    for d in deliveries:
        by_event.setdefault(d["event_id"], []).append(d)
    for e in events:
        e["deliveries"] = by_event.get(e["id"], [])
    received = _q("SELECT id, ts, event_type, signature_valid FROM integration_received ORDER BY id DESC LIMIT 20")
    return {"connectors": integrations.connectors(), "events": events, "received": received,
            "counts": {"events": _one("SELECT count(*) AS n FROM integration_events")["n"],
                       "delivered": _one("SELECT count(*) AS n FROM integration_deliveries WHERE status='delivered'")["n"],
                       "failed": _one("SELECT count(*) AS n FROM integration_deliveries WHERE status IN ('failed','partial')")["n"]},
            "console_url": reports.console_url()}


class ToggleIn(BaseModel):
    enabled: bool


@router.post("/integrations/local-receiver")
async def toggle_local_receiver(body: ToggleIn) -> dict[str, Any]:
    with tx() as conn:
        conn.execute("UPDATE demo_flags SET enabled=? WHERE flag='integration_local_receiver'", (1 if body.enabled else 0,))
    bus.publish("integration", {"local_receiver": body.enabled})
    return {"ok": True, "enabled": body.enabled}


@router.post("/integrations/test")
async def integrations_test() -> dict[str, Any]:
    """Send a clearly labelled test event to every connected system (the person pressed the button)."""
    eid = integrations.record_event({"event_type": "integration.test", "ref": "test", "summary": "Test event from the Shifttrace console. No action needed.",
                                     "payload": {"note": "connectivity test"}, "session_id": None, "asset_id": "console"})
    results = await integrations.deliver(eid)
    return {"ok": True, "event_id": eid, "results": results}


@router.post("/integrations/retry/{event_id}")
async def integrations_retry(event_id: int, connector: str | None = None) -> dict[str, Any]:
    return {"ok": True, "results": await integrations.deliver(event_id, only=connector)}


@router.post("/integrations/receiver")
async def integrations_receiver(request: Request) -> dict[str, Any]:
    """The console's own test receiver: verifies the HMAC signature the way a real receiver would."""
    body = await request.body()
    valid = integrations.verify_local(body, request.headers.get("x-shifttrace-signature"))
    try:
        kind = json.loads(body).get("event_type")
    except ValueError:
        kind = None
    with tx() as conn:
        conn.execute("INSERT INTO integration_received(ts, event_type, signature_valid, body_json) VALUES (?,?,?,?)",
                     (utcnow(), kind, 1 if valid else 0, body.decode(errors="replace")[:20000]))
    if not valid:
        raise HTTPException(401, "bad signature")
    return {"ok": True, "signature_valid": True}


@router.get("/integrations/calendar.ics")
async def follow_ups_calendar():
    from fastapi.responses import Response
    rows = _q("SELECT * FROM follow_ups WHERE status='OPEN' ORDER BY due_date")
    return Response(integrations.ics(rows), media_type="text/calendar", headers={"content-disposition": "attachment; filename=shifttrace-follow-ups.ics"})


@router.get("/follow-ups/{follow_up_id}.ics")
async def follow_up_ics(follow_up_id: str):
    from fastapi.responses import Response
    rows = _q("SELECT * FROM follow_ups WHERE follow_up_id=?", (follow_up_id,))
    if not rows:
        raise HTTPException(404, "follow-up not found")
    return Response(integrations.ics(rows), media_type="text/calendar", headers={"content-disposition": f"attachment; filename={follow_up_id}.ics"})


class ConsoleTool(BaseModel):
    tool: str
    session_id: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)


def _console_registry(a: dict[str, Any]):
    return {
        "get_asset_history": lambda c: tools.get_asset_history(c, a.get("asset_id")),
        "get_previous_handoff": lambda c: tools.get_previous_handoff(c, a.get("asset_id")),
        "search_maintenance_manual": lambda c: tools.search_maintenance_manual(c, a["query"], a.get("asset_id")),
        "check_inventory": lambda c: tools.check_inventory(c, a["part"]),
        "reserve_spare_part": lambda c: tools.reserve_spare_part(c, a["part"], int(a.get("quantity", 1)), a.get("work_order_id")),
        "create_procurement_request": lambda c: tools.create_procurement_request(c, a["part"], int(a.get("quantity", 1)), a.get("work_order_id"), a.get("reason")),
        "update_work_order": lambda c: tools.update_work_order(c, a.get("work_order_id"), a.get("status"), a.get("note", ""), via="console"),
        "escalate_incident": lambda c: tools.escalate_incident(c, a.get("work_order_id"), a.get("severity", "medium"), a.get("reason", "")),
        "record_observation": lambda c: tools.record_observation(c, a["kind"], a["summary"], a.get("detail")),
        "record_reading": lambda c: tools.record_reading(c, a["reading"], a["value"], a.get("unit"), a.get("source", "technician")),
        "update_open_item": lambda c: tools.update_open_item(c, int(a["event_id"]), a["status"], a.get("note", "")),
        "create_shift_handoff": lambda c: tools.create_shift_handoff(c),
        "schedule_follow_up": lambda c: tools.schedule_follow_up(c, a["title"], a.get("due"), a.get("assignee")),
        "track_shipment": lambda c: tools.track_shipment(c, a.get("reference")),
        "create_stock_transfer": lambda c: tools.create_stock_transfer(c, a["part"], int(a["quantity"]), a["from_location"], a["to_location"], a.get("reason")),
        "get_training_module": lambda c: tools.get_training_module(c, a.get("module_id")),
        "record_training_answer": lambda c: tools.record_training_answer(c, a["question_id"], a["answer"], a.get("module_id")),
        "finish_training_module": lambda c: tools.finish_training_module(c, a.get("module_id")),
    }


@router.post("/console/tool")
async def console_tool(body: ConsoleTool) -> dict[str, Any]:
    reg = _console_registry(body.args)
    if body.tool not in reg:
        raise HTTPException(400, f"unknown tool {body.tool}")
    try:
        impl = reg[body.tool]
    except KeyError as e:
        raise HTTPException(400, f"missing argument {e}")
    return await tools.run_tool(body.tool, body.args, body.session_id, "console", impl)


# ----------------------------------------------------------------------------- sessions

def _ctx(session_id: str | None) -> SessionContext:
    conn = connect()
    try:
        return SessionContext.resolve(conn, session_id)
    finally:
        conn.close()


class StartSession(BaseModel):
    asset_id: str
    technician: str = Field(min_length=2, max_length=60)
    shift_label: str = Field(default="A shift", max_length=40)
    voice: bool = True
    task_id: str | None = Field(default=None, max_length=60)


@router.post("/sessions")
async def start_session(body: StartSession) -> dict[str, Any]:
    asset = _service(svc.get_asset, body.asset_id)
    offered = {t["id"]: t for t in packs.tasks_for_asset(asset)}
    task_id = body.task_id or packs.default_task_id(asset)
    if task_id not in offered:
        raise HTTPException(400, f"task {task_id!r} is not offered for {asset['asset_id']}; choose one of {sorted(offered)}")
    task = offered[task_id]
    with tx() as conn:
        for row in conn.execute("SELECT session_id FROM sessions WHERE status='ACTIVE'").fetchall():
            conn.execute("UPDATE sessions SET status='ENDED', ended_at=? WHERE session_id=?", (utcnow(), row["session_id"]))
        sid = next_id(conn, "session", "S-", 1001)
        capture.forget(sid)
        guard.forget(sid)
        conn.execute(
            "INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status, task_id) VALUES (?,?,?,?,?,?,?)",
            (sid, asset["asset_id"], body.technician.strip(), body.shift_label.strip(), utcnow(), "ACTIVE", task_id),
        )
        svc.record_evidence(conn, session_id=sid, asset_id=asset["asset_id"], event_type="system_record", source_type="cmms",
                            title=f"Session {sid} started by {body.technician.strip()} ({body.shift_label.strip()}): {task['label']}",
                            payload={"task_id": task_id})
    for stale in list(agora_sessions._sessions.keys()):
        await agora_sessions.stop(stale)
    out: dict[str, Any] = {"session_id": sid, "asset_id": asset["asset_id"], "task_id": task_id, "voice": None, "voice_error": None}
    if body.voice and not await tunnel.ensure_healthy():
        # Never start an agent that cannot reach its tools: it would answer from imagination.
        out["voice_error"] = (f"Maintenance tools are not reachable from Agora ({tunnel.state.get('error')}); "
                              "voice agent not started. Check the tunnel / network and try again.")
        with tx() as conn:
            svc.record_evidence(conn, session_id=sid, asset_id=asset["asset_id"], event_type="system_record", source_type="cmms",
                                title="Voice agent not started: tools unreachable", detail=out["voice_error"], status="error")
        bus.publish("session", {"session_id": sid})
        return out
    if body.voice:
        try:
            v = await agora_sessions.start(sid, asset, body.technician.strip(), body.shift_label.strip(), task)
            with tx() as conn:
                conn.execute("UPDATE sessions SET agent_id=?, channel=?, agent_config_json=? WHERE session_id=?",
                             (v["agent_id"], v["channel"], json.dumps(v["agent_config"]), sid))
                tts = (v["agent_config"].get("tts") or {}) if isinstance(v["agent_config"], dict) else {}
                svc.record_evidence(conn, session_id=sid, asset_id=asset["asset_id"], event_type="system_record", source_type="cmms",
                                    title=f"Agora agent {v['agent_id']} connected to SHIFTTRACE tools in {v.get('tools_linked_ms')} ms"
                                          f"{' (attempt ' + str(v.get('attempts')) + ')' if v.get('attempts', 1) > 1 else ''}; channel {v['channel']}",
                                    detail=f"TTS vendor={tts.get('vendor')} model={(tts.get('params') or {}).get('model')} voice={(tts.get('params') or {}).get('voiceId')}")
            out["voice"] = {k: v[k] for k in ("agent_id", "channel", "user_uid", "agent_uid", "app_id", "token")}
        except Exception as e:
            log.exception("voice start failed")
            out["voice_error"] = f"{type(e).__name__}: {e}"
            with tx() as conn:
                svc.record_evidence(conn, session_id=sid, asset_id=asset["asset_id"], event_type="system_record", source_type="cmms",
                                    title="Voice agent could not start", detail=out["voice_error"], status="error")
    bus.publish("session", {"session_id": sid})
    return out


@router.post("/sessions/{session_id}/voice/restart")
async def restart_voice(session_id: str) -> dict[str, Any]:
    """Start a fresh agent (new channel) for an ACTIVE maintenance session whose agent left or broke."""
    s = _one("SELECT * FROM sessions WHERE session_id=?", (session_id,))
    if not s or s["status"] != "ACTIVE":
        raise HTTPException(400, "session is not active")
    await agora_sessions.stop(session_id)
    if not await tunnel.ensure_healthy():
        return {"voice": None, "voice_error": f"Maintenance tools are not reachable from Agora ({tunnel.state.get('error')})."}
    asset = _service(svc.get_asset, s["asset_id"])
    try:
        v = await agora_sessions.start(session_id, asset, s["technician"], s["shift_label"] or "", packs.get_task(s.get("task_id")))
    except Exception as e:
        return {"voice": None, "voice_error": f"{type(e).__name__}: {e}"}
    with tx() as conn:
        conn.execute("UPDATE sessions SET agent_id=?, channel=?, agent_config_json=? WHERE session_id=?",
                     (v["agent_id"], v["channel"], json.dumps(v["agent_config"]), session_id))
        svc.record_evidence(conn, session_id=session_id, asset_id=s["asset_id"], event_type="system_record", source_type="cmms",
                            title=f"Voice agent restarted: {v['agent_id']} connected to tools in {v.get('tools_linked_ms')} ms")
    bus.publish("voice", {"session_id": session_id, "status": "RESTARTED"})
    return {"voice": {k: v[k] for k in ("agent_id", "channel", "user_uid", "agent_uid", "app_id", "token")}, "voice_error": None}


@router.get("/sessions")
async def list_sessions(asset_id: str | None = None) -> list[dict[str, Any]]:
    if asset_id:
        return _q("SELECT session_id, asset_id, technician, shift_label, started_at, ended_at, status, agent_id, summary FROM sessions WHERE asset_id=? ORDER BY started_at DESC", (asset_id,))
    return _q("SELECT session_id, asset_id, technician, shift_label, started_at, ended_at, status, agent_id, summary FROM sessions ORDER BY started_at DESC")


@router.get("/sessions/{session_id}")
async def session_detail(session_id: str) -> dict[str, Any]:
    s = _one("SELECT * FROM sessions WHERE session_id=?", (session_id,))
    if not s:
        raise HTTPException(404, "session not found")
    s["voice_running"] = agora_sessions.is_running(session_id)
    try:
        s["task"] = _task_view(packs.get_task(s.get("task_id")))
    except packs.PackError:
        s["task"] = None
    s["evidence"] = _q("SELECT * FROM evidence WHERE session_id=? ORDER BY ts, id", (session_id,))
    s["tool_actions"] = _q("SELECT * FROM tool_actions WHERE session_id=? ORDER BY id", (session_id,))
    s["transcripts"] = _q("SELECT * FROM transcripts WHERE session_id=? ORDER BY ts, id", (session_id,))
    s["procurement"] = _q("SELECT pr.*, p.name AS part_name FROM procurement_requests pr JOIN parts p ON p.part_id=pr.part_id WHERE pr.session_id=? ORDER BY created_at", (session_id,))
    s["handoff"] = _one("SELECT * FROM handoffs WHERE session_id=?", (session_id,))
    s["transfers"] = _q("SELECT t.*, p.name AS part_name FROM stock_transfers t JOIN parts p ON p.part_id=t.part_id WHERE t.session_id=? ORDER BY created_at", (session_id,))
    s["follow_ups"] = _q("SELECT * FROM follow_ups WHERE session_id=? ORDER BY created_at", (session_id,))
    return s


@router.post("/sessions/{session_id}/end")
async def end_session(session_id: str) -> dict[str, Any]:
    stopped = await agora_sessions.stop(session_id)
    with tx() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(404, "session not found")
        if row["status"] == "ACTIVE":
            conn.execute("UPDATE sessions SET status='ENDED', ended_at=? WHERE session_id=?", (utcnow(), session_id))
            svc.record_evidence(conn, session_id=session_id, asset_id=row["asset_id"], event_type="system_record", source_type="cmms",
                                title=f"Session {session_id} ended" + (" (agent stopped)" if stopped else ""))
    bus.publish("session", {"session_id": session_id})
    return {"ok": True, "agent_stopped": stopped}


class TranscriptIn(BaseModel):
    role: str
    text: str = Field(max_length=4000)
    turn_id: str | None = None
    final: bool = True


@router.post("/sessions/{session_id}/transcripts")
async def add_transcript(session_id: str, body: TranscriptIn) -> dict[str, Any]:
    role = body.role.lower()
    if role not in {"user", "agent", "system"}:
        raise HTTPException(400, "role must be user or agent")
    text = body.text.strip()
    if not text:
        return {"ok": True, "skipped": True}
    if role == "user" and text.startswith(("SYSTEM CHECK", "SYSTEM NOTICE", "The technician approved", "The technician declined")):
        role = "system"  # our own think() injections echo back as user transcripts; never treat them as the technician
    with tx() as conn:
        if not conn.execute("SELECT 1 FROM sessions WHERE session_id=?", (session_id,)).fetchone():
            raise HTTPException(404, "session not found")
        svc.add_transcript(conn, session_id, role, body.turn_id or f"t{utcnow()}", text, body.final)
    bus.publish("transcript", {"session_id": session_id, "role": role})
    if role == "agent" and body.final:
        asyncio.create_task(guard.check_agent_utterance(session_id, body.turn_id or "", text))
        asyncio.create_task(capture.on_agent_utterance(session_id, body.turn_id or ""))
    return {"ok": True}


@router.get("/sessions/{session_id}/transcript-events")
async def transcript_events(session_id: str, after: int = 0) -> list[dict[str, Any]]:
    return _q("SELECT * FROM transcript_events WHERE session_id=? AND id>? ORDER BY id", (session_id, after))


@router.post("/sessions/{session_id}/snapshot")
async def snapshot(session_id: str, request: Request) -> dict[str, Any]:
    data = await request.body()
    try:
        name = media.save_snapshot(session_id, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "media_ref": name}


@router.get("/sessions/{session_id}/agent-config")
async def agent_config(session_id: str) -> dict[str, Any]:
    s = _one("SELECT agent_id, channel, agent_config_json FROM sessions WHERE session_id=?", (session_id,))
    if not s:
        raise HTTPException(404, "session not found")
    return s


@router.post("/sessions/{session_id}/handoff")
async def handoff_from_console(session_id: str) -> dict[str, Any]:
    return await tools.run_tool("create_shift_handoff", {}, session_id, "console", lambda c: tools.create_shift_handoff(c))


@router.get("/handoffs")
async def handoffs(asset_id: str | None = None) -> list[dict[str, Any]]:
    if asset_id:
        return _q("SELECT * FROM handoffs WHERE asset_id=? ORDER BY created_at DESC", (asset_id,))
    return _q("SELECT * FROM handoffs ORDER BY created_at DESC")


@router.get("/handoffs/{handoff_id}")
async def handoff(handoff_id: str) -> dict[str, Any]:
    h = _one("SELECT * FROM handoffs WHERE handoff_id=?", (handoff_id,))
    if not h:
        raise HTTPException(404, "handoff not found")
    return h


_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/handoffs/{handoff_id}/report.html")
async def handoff_report_html(handoff_id: str, download: bool = False):
    from fastapi.responses import Response
    from . import reports
    body = reports.handoff_html(handoff_id)
    if body is None:
        raise HTTPException(404, "handoff not found")
    headers = {"content-disposition": f"attachment; filename=handoff-{handoff_id}.html"} if download else {}
    return Response(body, media_type="text/html; charset=utf-8", headers=headers)


@router.get("/handoffs/{handoff_id}/report.xlsx")
async def handoff_report_xlsx(handoff_id: str):
    from fastapi.responses import Response
    from . import reports
    body = reports.handoff_xlsx(handoff_id)
    if body is None:
        raise HTTPException(404, "handoff not found")
    return Response(body, media_type=_XLSX, headers={"content-disposition": f"attachment; filename=handoff-{handoff_id}.xlsx"})


@router.get("/reports/operations.xlsx")
async def operations_report():
    from fastapi.responses import Response
    from . import reports
    return Response(reports.operations_xlsx(), media_type=_XLSX, headers={"content-disposition": "attachment; filename=shifttrace-operations.xlsx"})


@router.get("/evidence/{event_id}")
async def evidence_item(event_id: int) -> dict[str, Any]:
    e = _one("SELECT * FROM evidence WHERE id=?", (event_id,))
    if not e:
        raise HTTPException(404, "not found")
    return e


_SAFE = re.compile(r"^[A-Za-z0-9._-]+\.jpg$")


@router.get("/media/{name}")
async def media_file(name: str):
    if not _SAFE.match(name):
        raise HTTPException(400, "bad name")
    path = settings.media_dir / name
    if not path.exists():
        raise HTTPException(404, "not found")
    return FileResponse(path, media_type="image/jpeg")


# ----------------------------------------------------------------------------- test feed (no machine needed)

@router.get("/testkit")
async def testkit_for(asset_id: str | None = None, task_id: str | None = None) -> dict[str, Any]:
    return testkit.for_session(asset_id, task_id)


@router.get("/testkit/media/{name}")
async def testkit_media(name: str):
    path = testkit.media_path(name)
    if not path:
        raise HTTPException(404, "not in the test kit")
    return FileResponse(path, media_type=testkit.TYPES[path.suffix.lower()])


# ----------------------------------------------------------------------------- demo controls

class FlagIn(BaseModel):
    flag: str
    enabled: bool


@router.get("/demo/flags")
async def get_flags() -> dict[str, bool]:
    return {r["flag"]: bool(r["enabled"]) for r in _q("SELECT * FROM demo_flags")}


@router.post("/demo/flags")
async def set_flag(body: FlagIn) -> dict[str, bool]:
    if body.flag not in {"inventory_outage", "supplier_rejects"}:
        raise HTTPException(400, "unknown flag")
    with tx() as conn:
        conn.execute("UPDATE demo_flags SET enabled=? WHERE flag=?", (int(body.enabled), body.flag))
    bus.publish("flags", None)
    return await get_flags()


@router.post("/demo/reset")
async def demo_reset() -> dict[str, Any]:
    for sid in list(agora_sessions._sessions.keys()):
        await agora_sessions.stop(sid)
    packs.reload_tasks()
    testkit.reload()
    capture.forget()
    guard.forget()
    reset_database()
    bus.publish("reset", None)
    return {"ok": True}


# ----------------------------------------------------------------------------- SSE

@router.get("/stream")
async def stream(request: Request):
    q = bus.subscribe()

    async def gen():
        try:
            yield "event: hello\ndata: {}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            bus.unsubscribe(q)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def create_app() -> FastAPI:
    app = FastAPI(title="SHIFTTRACE console API", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                       allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, bool]:
        return {"ok": True}

    # Hosted deployments (the console is local-only by default) must set CONSOLE_PASSWORD: the console has no user
    # accounts and can start paid Agora sessions. HTTP Basic auth, any user name. The MCP path has its own bearer token
    # and is served by a separate app, and the local test receiver checks its own HMAC signature.
    password = settings.console_password
    if password:
        import base64
        import hmac as _hmac
        open_paths = ("/healthz", "/api/integrations/receiver")
        # The product page and the 3D floor view are public, with the read-only data they show (synthetic demo data).
        # Everything that changes something, starts a voice session or configures the site stays behind the password.
        public_pages = ("/", "/floor", "/favicon.ico")
        public_reads = ("/api/assets", "/api/tool-actions", "/api/sessions", "/api/handoffs", "/api/costs", "/api/stream")

        def _is_public(request: Request) -> bool:
            path = request.url.path
            if path in open_paths:
                return True
            if request.method not in ("GET", "HEAD"):
                return False
            return path in public_pages or path in public_reads or path.startswith("/assets/") or path.startswith("/api/testkit/media/")

        @app.middleware("http")
        async def _console_auth(request: Request, call_next):
            if _is_public(request):
                return await call_next(request)
            auth = request.headers.get("authorization", "")
            ok = False
            if auth.lower().startswith("basic "):
                try:
                    supplied = base64.b64decode(auth[6:]).decode("utf-8", "replace").split(":", 1)[-1]
                    ok = _hmac.compare_digest(supplied.encode(), password.encode())
                except ValueError:
                    ok = False
            if not ok:
                return JSONResponse(status_code=401, content={"error": "console password required"},
                                    headers={"WWW-Authenticate": 'Basic realm="Shifttrace console", charset="UTF-8"'})
            return await call_next(request)

    @app.exception_handler(ServiceError)
    async def _svc_err(_: Request, exc: ServiceError):
        return JSONResponse(status_code=400, content=exc.to_dict())

    dist = settings.frontend_dist
    if (dist / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        async def spa(path: str):
            candidate = (dist / path).resolve()
            if path and candidate.is_file() and dist.resolve() in candidate.parents:
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")
    return app
