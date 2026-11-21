"""FastMCP server exposed to Agora Conversational AI (Agora cloud is the MCP client).

Transport: streamable HTTP at /mcp on its own port (MCP_PORT), published through a
tunnel. Every request must carry `Authorization: Bearer <MCP_TOKEN>`; the agent's
maintenance session is bound with the `X-Shifttrace-Session` header that we set in
the agent's mcp_servers config when the session starts.
"""
from __future__ import annotations

import hmac
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from . import tools
from .config import settings

# Requests arrive through a public tunnel, so the Host header is the tunnel's hostname.
# FastMCP's default DNS-rebinding guard only admits localhost and would reject Agora;
# the per-run bearer token (BearerAuth below) is the access control instead.
mcp = FastMCP(
    "shifttrace",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

CORE_TOOLS = [  # offered to every task that does not list its own tools
    "get_asset_history", "get_open_work_orders", "get_previous_handoff", "get_open_items",
    "search_maintenance_manual", "check_inventory", "reserve_spare_part", "create_procurement_request",
    "approve_procurement_request", "update_work_order", "escalate_incident", "record_observation", "record_reading",
    "update_open_item", "create_shift_handoff", "schedule_follow_up",
]
DOMAIN_TOOLS = [  # opt-in per task (tasks.json "tools")
    "track_shipment", "create_stock_transfer", "confirm_stock_transfer",          # warehouse and logistics
    "get_training_module", "record_training_answer", "finish_training_module",    # training and onboarding
]
TOOL_NAMES = CORE_TOOLS + DOMAIN_TOOLS


def _session(ctx: Context | None) -> str | None:
    try:
        req = ctx.request_context.request if ctx else None
        return req.headers.get("x-shifttrace-session") if req is not None else None
    except Exception:
        return None


async def _run(name: str, args: dict[str, Any], ctx: Context | None, impl) -> dict[str, Any]:
    return await tools.run_tool(name, args, _session(ctx), "agora_mcp", impl)


@mcp.tool()
async def get_asset_history(asset_id: str | None = None, ctx: Context = None) -> dict:
    """Retrieve the machine's maintenance memory: asset details, work orders with their log, recent technician
    sessions, and recent evidence (observations, statements, hypotheses) with their source. Use when the technician
    asks what happened to the machine, its history, or before troubleshooting. asset_id defaults to the session's asset."""
    return await _run("get_asset_history", {"asset_id": asset_id}, ctx, lambda c: tools.get_asset_history(c, asset_id))


@mcp.tool()
async def get_open_work_orders(asset_id: str | None = None, ctx: Context = None) -> dict:
    """List open (not resolved/closed) work orders for the asset, with status, priority and recent log notes."""
    return await _run("get_open_work_orders", {"asset_id": asset_id}, ctx, lambda c: tools.get_open_work_orders(c, asset_id))


@mcp.tool()
async def get_previous_handoff(asset_id: str | None = None, ctx: Context = None) -> dict:
    """Get the most recent shift handoff for the asset from a previous session: headline, observations, verified
    actions, ruled-out causes, open loops and suggested next steps. Use for 'what happened on the previous shift',
    'what did we try', 'what is still open'. Answer only from this record."""
    return await _run("get_previous_handoff", {"asset_id": asset_id}, ctx, lambda c: tools.get_previous_handoff(c, asset_id))


@mcp.tool()
async def get_open_items(asset_id: str | None = None, ctx: Context = None) -> dict:
    """List unresolved hypotheses and open questions (open loops) for the asset, with their event_id."""
    return await _run("get_open_items", {"asset_id": asset_id}, ctx, lambda c: tools.get_open_items(c, asset_id))


@mcp.tool()
async def search_maintenance_manual(query: str, asset_id: str | None = None, ctx: Context = None) -> dict:
    """Search the asset's service manual. Returns up to 3 sections with section number and text. Quote the section
    number when you use it (for example 'manual section 6.3'). Use for alarm codes, limits, procedures, part numbers."""
    return await _run("search_maintenance_manual", {"query": query, "asset_id": asset_id}, ctx,
                      lambda c: tools.search_maintenance_manual(c, query, asset_id))


@mcp.tool()
async def check_inventory(part: str, ctx: Context = None) -> dict:
    """Check stores stock for a spare part by part ID or description (for example 'BRG-6316-C3' or 'drive end
    bearing'). Returns available quantity, location, lead time and any open procurement requests for that part."""
    return await _run("check_inventory", {"part": part}, ctx, lambda c: tools.check_inventory(c, part))


@mcp.tool()
async def reserve_spare_part(part: str, quantity: int = 1, work_order_id: str | None = None, ctx: Context = None) -> dict:
    """Reserve an IN-STOCK spare part in stores against a work order (defaults to the asset's open work order).
    Idempotent: repeating the call does not double-reserve. Fails if stock is insufficient."""
    return await _run("reserve_spare_part", {"part": part, "quantity": quantity, "work_order_id": work_order_id}, ctx,
                      lambda c: tools.reserve_spare_part(c, part, quantity, work_order_id))


@mcp.tool()
async def create_procurement_request(part: str, quantity: int = 1, work_order_id: str | None = None,
                                     reason: str | None = None, ctx: Context = None) -> dict:
    """Create a DRAFT procurement request for an out-of-stock part. This does NOT order anything. After calling,
    read back part, quantity and work order and ask the technician to confirm. Idempotent: an existing open request
    for the same part and work order is returned instead of a duplicate."""
    return await _run("create_procurement_request", {"part": part, "quantity": quantity, "work_order_id": work_order_id, "reason": reason},
                      ctx, lambda c: tools.create_procurement_request(c, part, quantity, work_order_id, reason))


@mcp.tool()
async def approve_procurement_request(request_id: str, ctx: Context = None) -> dict:
    """Submit a drafted procurement request to the supplier. Call ONLY after the technician has explicitly said yes
    to the draft you read back. The server independently checks the technician's own words; if it returns
    APPROVAL_REQUIRED, nothing was ordered and you must ask again. Only say it was ordered if verified is true."""
    return await _run("approve_procurement_request", {"request_id": request_id}, ctx,
                      lambda c: tools.approve_procurement_request(c, request_id))


@mcp.tool()
async def update_work_order(note: str, status: str | None = None, work_order_id: str | None = None, ctx: Context = None) -> dict:
    """Add a note to a work order and optionally change its status. Allowed statuses: OPEN, IN_PROGRESS,
    WAITING_PARTS, ESCALATED (RESOLVED/CLOSED need supervisor sign-off in the console). Defaults to the asset's
    open work order. Report the verified status that comes back."""
    return await _run("update_work_order", {"work_order_id": work_order_id, "status": status, "note": note}, ctx,
                      lambda c: tools.update_work_order(c, work_order_id, status, note))


@mcp.tool()
async def escalate_incident(reason: str, severity: str = "medium", work_order_id: str | None = None, ctx: Context = None) -> dict:
    """Raise an escalation to the shift supervisor (severity low, medium or high) with a reason. Use when the
    technician asks to escalate or reports a safety concern."""
    return await _run("escalate_incident", {"work_order_id": work_order_id, "severity": severity, "reason": reason}, ctx,
                      lambda c: tools.escalate_incident(c, work_order_id, severity, reason))


@mcp.tool()
async def record_observation(kind: str, summary: str, detail: str | None = None, ctx: Context = None) -> dict:
    """Write an item into the machine's evidence timeline. kind is one of:
    'visual' = what you can see in the technician's camera right now (describe only what is visible, e.g. 'TEMP HIGH
    lamp appears lit, display reads A-17 108 C'); 'technician_report' = something the technician stated (readings,
    sounds, what they did), quote them; 'hypothesis' = a possible cause worth checking (never a diagnosis);
    'open_question' = something nobody has answered yet. Keep summary under 15 words."""
    return await _run("record_observation", {"kind": kind, "summary": summary, "detail": detail}, ctx,
                      lambda c: tools.record_observation(c, kind, summary, detail))


@mcp.tool()
async def record_reading(reading: str, value: float, unit: str | None = None, source: str = "technician",
                         ctx: Context = None) -> dict:
    """Record a NUMERIC reading (pressure, temperature, current, vibration, speed...) and check it against this
    machine's configured limits. Use this instead of record_observation whenever there is a number. reading = what
    was measured (e.g. 'bag filter differential pressure', 'fan motor current'); value = the number only; unit as
    spoken ('Pa', 'amps', 'C', 'mm/s'); source = 'technician' if they said it, 'camera' if you read it on the display.
    Returns evaluation normal / outside_normal / out_of_limit and a 'say' sentence; out-of-limit readings are logged
    for follow-up automatically. Report the evaluation from the result; never compare numbers yourself."""
    return await _run("record_reading", {"reading": reading, "value": value, "unit": unit, "source": source}, ctx,
                      lambda c: tools.record_reading(c, reading, value, unit, source))


@mcp.tool()
async def update_open_item(event_id: int, status: str, note: str, ctx: Context = None) -> dict:
    """Close an open loop (hypothesis or open question) by event_id when the technician gives evidence:
    status 'confirmed', 'ruled_out' or 'answered', with a note saying why."""
    return await _run("update_open_item", {"event_id": event_id, "status": status, "note": note}, ctx,
                      lambda c: tools.update_open_item(c, event_id, status, note))


@mcp.tool()
async def create_shift_handoff(ctx: Context = None) -> dict:
    """Generate and store the shift handoff for the current session from persisted records only (observations,
    verified actions, failures, parts, open loops). Use when the technician asks to prepare the handoff or ends
    the shift. Then speak the spoken_summary briefly."""
    return await _run("create_shift_handoff", {}, ctx, lambda c: tools.create_shift_handoff(c))


@mcp.tool()
async def schedule_follow_up(title: str, due: str | None = None, assignee: str | None = None, ctx: Context = None) -> dict:
    """Schedule a follow-up task so something is not forgotten: a re-check, a recount, a part to fit, a call to make,
    a retraining session. title = what needs doing (under 12 words); due = when, as spoken ('tomorrow', 'next shift',
    'Friday', '2026-11-24'); assignee = who (default 'next shift'). Only schedule what the worker asked for or agreed to."""
    return await _run("schedule_follow_up", {"title": title, "due": due, "assignee": assignee}, ctx,
                      lambda c: tools.schedule_follow_up(c, title, due, assignee))


@mcp.tool()
async def track_shipment(reference: str | None = None, ctx: Context = None) -> dict:
    """Look up inbound or outbound shipments in the carrier tracking record: status, last scan, ETA, items on board.
    reference = a shipment ID ('SHP-4471' or just '4471'), the carrier's reference, or an item name on board
    ('the rice delivery'). Leave empty to list shipments for this site."""
    return await _run("track_shipment", {"reference": reference}, ctx, lambda c: tools.track_shipment(c, reference))


@mcp.tool()
async def create_stock_transfer(part: str, quantity: int, from_location: str, to_location: str, reason: str | None = None,
                                ctx: Context = None) -> dict:
    """DRAFT a stock transfer between two locations (for example replenishing a pick face from reserve). This does NOT
    move anything. part = SKU or item name; from_location / to_location = location IDs as spoken ('reserve R 12',
    'bin B 04 2'). Then read back item, quantity, from and to, and ask the worker to confirm."""
    return await _run("create_stock_transfer", {"part": part, "quantity": quantity, "from_location": from_location,
                                                "to_location": to_location, "reason": reason}, ctx,
                      lambda c: tools.create_stock_transfer(c, part, int(quantity), from_location, to_location, reason))


@mcp.tool()
async def confirm_stock_transfer(transfer_id: str, ctx: Context = None) -> dict:
    """Carry out a drafted stock transfer and post it to the ERP. Only succeeds if the WORKER said yes out loud after
    your read-back (checked against the live transcript) or pressed Confirm in the console; otherwise it returns
    APPROVAL_REQUIRED and nothing moves. Never call it in the same turn as the draft. Say it is moved only if verified."""
    return await _run("confirm_stock_transfer", {"transfer_id": transfer_id}, ctx, lambda c: tools.confirm_stock_transfer(c, transfer_id))


@mcp.tool()
async def get_training_module(module_id: str | None = None, ctx: Context = None) -> dict:
    """Start a training or onboarding module for this machine or site: returns its title, pass mark and the questions
    to ask (with the manual section each one covers) and the trainee's previous result. module_id defaults to the first
    module configured for this asset."""
    return await _run("get_training_module", {"module_id": module_id}, ctx, lambda c: tools.get_training_module(c, module_id))


@mcp.tool()
async def record_training_answer(question_id: str, answer: str, module_id: str | None = None, ctx: Context = None) -> dict:
    """Record the trainee's spoken answer to one training question. The answer is marked in code against the key
    points configured for the question (correct, partly, incorrect) - never mark it yourself. answer = the trainee's
    words, as close to verbatim as possible. Use 'explain' and 'section' from the result to teach the right answer."""
    return await _run("record_training_answer", {"question_id": question_id, "answer": answer, "module_id": module_id}, ctx,
                      lambda c: tools.record_training_answer(c, question_id, answer, module_id))


@mcp.tool()
async def finish_training_module(module_id: str | None = None, ctx: Context = None) -> dict:
    """Finish the module: computes the score from the recorded answers (unanswered questions count as zero), applies
    the pass mark, and updates the trainee's learning record. Report the score and status exactly as returned."""
    return await _run("finish_training_module", {"module_id": module_id}, ctx, lambda c: tools.finish_training_module(c, module_id))


# session_id -> monotonic time of the most recent authenticated MCP request carrying that session header.
# Used to verify that Agora actually connected to the tools after an agent starts.
mcp_links: dict[str, float] = {}


class BearerAuth:
    """Pure-ASGI guard: only callers with the per-run MCP token reach the tools."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            supplied = headers.get("authorization", "")
            expected = f"Bearer {settings.mcp_token}"
            if not hmac.compare_digest(supplied.encode(), expected.encode()):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
            sid = headers.get("x-shifttrace-session")
            if sid:
                import time
                mcp_links[sid] = time.monotonic()
        await self.app(scope, receive, send)


def build_mcp_asgi():
    starlette_app = mcp.streamable_http_app()
    return starlette_app, BearerAuth(starlette_app)
