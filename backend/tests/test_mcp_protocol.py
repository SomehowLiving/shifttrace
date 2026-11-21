"""Talk to the real MCP ASGI app over HTTP, the way Agora cloud does."""
import asyncio
import socket
import threading
import time

import httpx
import pytest
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.db import tx, utcnow
from app.mcp_server import TOOL_NAMES, build_mcp_asgi


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def mcp_url():
    port = _free_port()
    _, app = build_mcp_asgi()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/mcp"
    server.should_exit = True
    t.join(timeout=5)


def test_rejects_missing_token(mcp_url):
    r = httpx.post(mcp_url, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                   headers={"Accept": "application/json, text/event-stream"})
    assert r.status_code == 401


def test_accepts_tunnel_host_header(mcp_url):
    """Agora reaches us through a tunnel; a non-localhost Host header must not be rejected."""
    r = httpx.post(mcp_url, json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                  "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}},
                   headers={"Accept": "application/json, text/event-stream", "Authorization": "Bearer test-token",
                            "Host": "example.trycloudflare.com"})
    assert r.status_code == 200, r.text


def test_list_and_call_tools_with_session_header(mcp_url):
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status) VALUES ('S-1001','C-204','Kavya Rao','A shift',?, 'ACTIVE')", (utcnow(),))

    async def go():
        headers = {"Authorization": "Bearer test-token", "X-Shifttrace-Session": "S-1001"}
        async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                names = sorted(t.name for t in listed.tools)
                assert names == sorted(TOOL_NAMES)
                res = await session.call_tool("check_inventory", {"part": "drive end bearing"})
                assert not res.isError
                res2 = await session.call_tool("record_observation", {"kind": "visual", "summary": "TEMP HIGH lamp appears lit"})
                return res, res2

    res, res2 = asyncio.run(go())
    text = res.content[0].text
    assert "BRG-6316-C3" in text
    with tx() as conn:
        row = conn.execute("SELECT session_id, caller FROM tool_actions WHERE tool_name='record_observation'").fetchone()
        ev = conn.execute("SELECT session_id, source_type, model_id FROM evidence WHERE event_type='visual_observation' AND session_id='S-1001'").fetchone()
    assert row["session_id"] == "S-1001" and row["caller"] == "agora_mcp"
    assert ev["source_type"] == "camera_model" and "Agora" in ev["model_id"]
