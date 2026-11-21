"""Entrypoint: console API on API_PORT (localhost) + MCP server on MCP_PORT (the only tunnelled port).

    uv run python -m app.main
"""
from __future__ import annotations

import asyncio
import logging

import uvicorn

from . import tunnel
from .api import create_app
from .bus import bus
from .config import settings
from .db import connect, init_schema
from .mcp_server import build_mcp_asgi
from .seed import reset_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("shifttrace")


def ensure_db() -> None:
    if not settings.db_path.exists():
        reset_database()
        log.info("seeded new database at %s", settings.db_path)
        return
    conn = connect()
    try:
        init_schema(conn)
    finally:
        conn.close()


async def on_tunnel(kind: str, info: dict) -> None:
    """Tell every live agent (and the timeline) when its tools become unreachable or come back."""
    from . import services as svc
    from .agora_session import agora_sessions
    from .db import tx

    msgs = {
        "down": ("Maintenance tools unreachable from Agora (tunnel down)",
                 "SYSTEM NOTICE: the maintenance system is unreachable. Do not claim to look up, record, order or update "
                 "anything. If asked, say you cannot reach the maintenance system right now and nothing was changed."),
        "up": ("Maintenance tools reachable again", "SYSTEM NOTICE: the maintenance system is reachable again; you may use tools."),
        "url_changed": ("Tool endpoint moved; this voice session can no longer reach tools (restart the session)",
                        "SYSTEM NOTICE: your connection to the maintenance system was lost permanently in this call. Tell the "
                        "technician to end and restart the session; until then do not claim any lookup or action."),
    }
    if kind not in msgs:
        return
    title, note = msgs[kind]
    for sid in list(agora_sessions._sessions):
        with tx() as conn:
            row = conn.execute("SELECT asset_id FROM sessions WHERE session_id=?", (sid,)).fetchone()
            svc.record_evidence(conn, session_id=sid, asset_id=row["asset_id"] if row else svc.fallback_asset_id(conn), event_type="system_record",
                                source_type="cmms", title=title, detail=str(info), status="error" if kind != "up" else None)
        await agora_sessions.think(sid, note)
    bus.publish("tunnel", {"kind": kind, **info})


async def voice_monitor() -> None:
    """Notice when Agora's agent has left (e.g. 'Idle for too long' after a network outage) and tell the console."""
    from . import services as svc
    from .agora_session import agora_sessions
    from .db import tx

    while True:
        await asyncio.sleep(15)
        for sid in list(agora_sessions._sessions):
            info = await agora_sessions.info(sid)
            if not info or info["status"] in ("RUNNING", "STARTING", "UNKNOWN", "IDLE"):
                continue
            agora_sessions.forget(sid)
            with tx() as conn:
                row = conn.execute("SELECT asset_id, status FROM sessions WHERE session_id=?", (sid,)).fetchone()
                if row and row["status"] == "ACTIVE":
                    svc.record_evidence(conn, session_id=sid, asset_id=row["asset_id"], event_type="system_record", source_type="cmms",
                                        title=f"Voice agent left the call ({info['status']}): {info.get('message') or 'no reason given'}",
                                        detail="Use 'Restart voice agent' to continue this session.", status="error")
            bus.publish("voice", {"session_id": sid, "status": info["status"], "message": info.get("message")})
            log.warning("agent for %s ended: %s %s", sid, info["status"], info.get("message"))


class _Dispatch:
    """One ASGI app for hosted mode: /mcp goes to the MCP server (bearer token), everything else to the console."""

    def __init__(self, api, mcp_app) -> None:
        self.api, self.mcp = api, mcp_app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] in ("http", "websocket") and (scope.get("path") == "/mcp" or scope.get("path", "").startswith("/mcp/")):
            await self.mcp(scope, receive, send)
        else:
            await self.api(scope, receive, send)


async def serve_single() -> None:
    """Hosted mode: console + MCP on $PORT, bound to all interfaces. No tunnel: MCP_PUBLIC_URL is the service URL."""
    ensure_db()
    if not settings.console_password:
        raise SystemExit("CONSOLE_PASSWORD must be set when the console is hosted (SHIFTTRACE_SINGLE_PORT=1).")
    bus.bind(asyncio.get_running_loop())
    tunnel.listeners.append(on_tunnel)
    starlette_mcp, mcp_asgi = build_mcp_asgi()
    app = _Dispatch(create_app(), mcp_asgi)
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=settings.api_port, log_level="info", lifespan="off",
                                           proxy_headers=True, forwarded_allow_ips="*"))
    log.info("hosted mode on port %s (console + /mcp); public URL %s", settings.api_port, settings.mcp_public_url or "(not set)")
    log.info("readiness    %s", settings.readiness())

    async def probe_later() -> None:
        await asyncio.sleep(5)  # let the server start listening before the public probe
        await tunnel.start()

    async with starlette_mcp.router.lifespan_context(starlette_mcp):  # starts the MCP session manager
        await asyncio.gather(server.serve(), probe_later(), voice_monitor())


async def serve() -> None:
    ensure_db()
    bus.bind(asyncio.get_running_loop())
    tunnel.listeners.append(on_tunnel)
    api_app = create_app()
    _, mcp_asgi = build_mcp_asgi()
    api_server = uvicorn.Server(uvicorn.Config(api_app, host="127.0.0.1", port=settings.api_port, log_level="info"))
    mcp_server = uvicorn.Server(uvicorn.Config(mcp_asgi, host="127.0.0.1", port=settings.mcp_port, log_level="info",
                                               proxy_headers=True, forwarded_allow_ips="127.0.0.1"))
    log.info("console API  http://127.0.0.1:%s", settings.api_port)
    log.info("MCP server   http://127.0.0.1:%s/mcp", settings.mcp_port)
    log.info("readiness    %s", settings.readiness())
    try:
        await asyncio.gather(api_server.serve(), mcp_server.serve(), tunnel.start(), voice_monitor())
    finally:
        await tunnel.stop()


if __name__ == "__main__":
    asyncio.run(serve_single() if settings.single_port else serve())
