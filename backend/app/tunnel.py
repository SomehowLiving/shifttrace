"""Public reachability of the MCP port (the only thing Agora cloud must reach).

* Auto-starts a Cloudflare quick tunnel unless MCP_PUBLIC_URL is set (or AUTO_TUNNEL=0).
* Watchdog: probes `<public>/mcp` with an MCP `initialize` every WATCH_S seconds. A quick tunnel can die
  silently while `cloudflared` keeps running (observed 19 Nov: the agent then had NO tools and invented
  results). After 2 consecutive failures the quick tunnel is restarted (new URL) and listeners are told.
* ensure_healthy(): on-demand gate used before starting any voice agent.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import time
from pathlib import Path
from typing import Awaitable, Callable

import httpx

from .config import settings

log = logging.getLogger("shifttrace.tunnel")
_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
WATCH_S = float(os.getenv("TUNNEL_WATCH_S", "20"))

state: dict[str, object] = {"mode": "none", "url": None, "self_test": None, "healthy": None, "checked_at": None,
                            "consecutive_failures": 0, "restarts": 0, "error": None}
_proc: asyncio.subprocess.Process | None = None
_lock = asyncio.Lock()
Listener = Callable[[str, dict], Awaitable[None]]
listeners: list[Listener] = []  # called with ("down"|"up"|"url_changed", info)


def _binary() -> str | None:
    found = shutil.which("cloudflared")
    if found:
        return found
    for p in (r"C:\Program Files (x86)\cloudflared\cloudflared.exe", r"C:\Program Files\cloudflared\cloudflared.exe"):
        if Path(p).exists():
            return p
    return None


async def probe(base_url: str | None, timeout: float = 8) -> bool:
    """One MCP initialize through the public URL, exactly as Agora would call it."""
    if not base_url:
        return False
    body = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "shifttrace-probe", "version": "1"}}}
    headers = {"Authorization": f"Bearer {settings.mcp_token}", "Accept": "application/json, text/event-stream",
               "ngrok-skip-browser-warning": "1"}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{base_url}/mcp", json=body, headers=headers)
        ok = r.status_code == 200 and "shifttrace" in r.text
        state["error"] = None if ok else f"probe HTTP {r.status_code}"
        return ok
    except httpx.HTTPError as e:
        state["error"] = f"probe {type(e).__name__}"
        return False


async def _record(ok: bool) -> None:
    """Health is 'down' only after 2 consecutive failed probes: a single transient failure once made the
    live agent tell the technician the system was unreachable when it was not (observed 20 Nov)."""
    state["self_test"] = ok
    state["checked_at"] = time.time()
    state["consecutive_failures"] = 0 if ok else int(state["consecutive_failures"]) + 1  # type: ignore[arg-type]
    was = state.get("healthy")
    now_healthy = ok or int(state["consecutive_failures"]) < 2  # type: ignore[arg-type]
    state["healthy"] = now_healthy
    if was is not None and was != now_healthy:
        if not now_healthy:
            state["down_announced_at"] = time.time()
        await _notify("up" if now_healthy else "down", {"url": state["url"]})


async def _notify(kind: str, info: dict) -> None:
    for fn in list(listeners):
        try:
            await fn(kind, info)
        except Exception:
            log.exception("tunnel listener failed")


async def _start_quick() -> bool:
    global _proc
    exe = _binary()
    if not exe:
        state.update(mode="unavailable", error="cloudflared not installed")
        return False
    if _proc and _proc.returncode is None:
        _proc.terminate()
        try:
            await asyncio.wait_for(_proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            _proc.kill()
    _proc = await asyncio.create_subprocess_exec(
        exe, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{settings.mcp_port}",
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
    state["mode"] = "cloudflared-quick"
    assert _proc.stderr is not None
    try:
        while True:
            line = await asyncio.wait_for(_proc.stderr.readline(), timeout=45)
            if not line:
                raise RuntimeError("cloudflared exited")
            m = _URL.search(line.decode(errors="replace"))
            if m:
                break
    except Exception as e:
        state["error"] = f"tunnel failed: {e}"
        log.error("tunnel failed: %s", e)
        return False
    asyncio.create_task(_drain(_proc.stderr))
    old = settings.mcp_public_url
    settings.mcp_public_url = m.group(0)
    state["url"] = m.group(0)
    log.info("tunnel up: %s", settings.mcp_public_url)
    for attempt in range(12):  # new hostnames take a few seconds to resolve
        if await probe(settings.mcp_public_url):
            await _record(True)
            log.info("tunnel MCP self-test: PASS")
            if old and old != settings.mcp_public_url:
                await _notify("url_changed", {"old": old, "new": settings.mcp_public_url})
            return True
        await asyncio.sleep(2 + attempt)
    await _record(False)
    log.error("tunnel MCP self-test: FAIL (%s)", state["error"])
    return False


def _ngrok_binary() -> str | None:
    found = shutil.which("ngrok")
    if found:
        return found
    base = Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    for p in base.glob("Ngrok.Ngrok_*/ngrok.exe"):
        return str(p)
    return None


async def _start_ngrok() -> bool:
    """ngrok with a reserved free static domain: the public URL survives restarts, so a running agent
    keeps its tools even if the tunnel process has to be restarted."""
    global _proc
    exe = _ngrok_binary()
    domain = os.getenv("NGROK_DOMAIN", "").strip().removeprefix("https://").rstrip("/")
    if not exe:
        state.update(mode="unavailable", error="ngrok not installed")
        return False
    if _proc and _proc.returncode is None:
        _proc.terminate()
        try:
            await asyncio.wait_for(_proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            _proc.kill()
    args = [exe, "http", str(settings.mcp_port), "--log", "stdout", "--log-format", "json"]
    if domain:
        args.append(f"--url=https://{domain}")
    env = {**os.environ, "NGROK_AUTHTOKEN": os.getenv("NGROK_AUTHTOKEN", "")}  # token via env, never argv
    _proc = await asyncio.create_subprocess_exec(*args, env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    state["mode"] = "ngrok"
    assert _proc.stdout is not None
    url = None
    try:
        while url is None:
            line = await asyncio.wait_for(_proc.stdout.readline(), timeout=45)
            if not line:
                raise RuntimeError("ngrok exited")
            try:
                rec = json.loads(line.decode(errors="replace"))
            except json.JSONDecodeError:
                continue
            # ngrok attaches `err` to harmless info/debug lines (e.g. "no config file"); only error levels are fatal.
            if rec.get("lvl") in ("eror", "crit"):
                raise RuntimeError(str(rec.get("err") or rec.get("msg"))[:300])
            if rec.get("msg") == "started tunnel" and rec.get("url"):
                url = rec["url"]
    except Exception as e:
        state["error"] = f"ngrok failed: {e}"
        log.error("ngrok failed: %s", e)
        return False
    asyncio.create_task(_drain(_proc.stdout))
    old = settings.mcp_public_url
    settings.mcp_public_url = url.rstrip("/")
    state["url"] = settings.mcp_public_url
    log.info("tunnel up (ngrok): %s", settings.mcp_public_url)
    for attempt in range(8):
        if await probe(settings.mcp_public_url):
            await _record(True)
            log.info("tunnel MCP self-test: PASS")
            if old and old != settings.mcp_public_url:
                await _notify("url_changed", {"old": old, "new": settings.mcp_public_url})
            return True
        await asyncio.sleep(2 + attempt)
    await _record(False)
    log.error("tunnel MCP self-test: FAIL (%s)", state["error"])
    return False


def _ngrok_alive() -> bool:
    return bool(state["mode"] == "ngrok" and _proc and _proc.returncode is None)


async def _start_ngrok_retrying() -> bool:
    """Restarting ngrok on a static domain right after the old session dropped fails with 'endpoint is already
    online' until ngrok's cloud releases it (observed 21 Nov). Wait and retry instead of giving up."""
    for attempt in range(4):
        if await _start_ngrok():
            return True
        if "already online" not in str(state.get("error") or ""):
            return False
        log.warning("ngrok domain still held by the previous session; retrying in %ss", 6 + 4 * attempt)
        await asyncio.sleep(6 + 4 * attempt)
    return False


async def _restart() -> bool:
    state["restarts"] = int(state["restarts"]) + 1  # type: ignore[arg-type]
    if state["mode"] == "ngrok":
        return await _start_ngrok_retrying()
    if state["mode"] == "cloudflared-quick":
        return await _start_quick()
    return False


async def start() -> None:
    if settings.mcp_public_url:
        state.update(mode="manual", url=settings.mcp_public_url)
        await _record(await probe(settings.mcp_public_url))
        log.info("manual MCP URL self-test: %s", "PASS" if state["healthy"] else "FAIL")
    elif os.getenv("AUTO_TUNNEL", "1") == "0":
        state["mode"] = "disabled"
    elif os.getenv("NGROK_AUTHTOKEN", "").strip():
        async with _lock:
            if not await _start_ngrok_retrying():
                log.warning("ngrok unavailable; falling back to a Cloudflare quick tunnel")
                await _start_quick()
    else:
        async with _lock:
            await _start_quick()
    asyncio.create_task(_watchdog())


async def _watchdog() -> None:
    while True:
        await asyncio.sleep(WATCH_S)
        if not state.get("url"):
            continue
        async with _lock:
            await _record(await probe(str(state["url"])))
            # A live ngrok process on a static domain usually means a network blip, not a dead tunnel: restarting it
            # makes things worse (the domain is still held). Give it longer before restarting.
            limit = 5 if _ngrok_alive() else 2
            if state["mode"] in ("cloudflared-quick", "ngrok") and int(state["consecutive_failures"]) >= limit:  # type: ignore[arg-type]
                log.warning("tunnel unhealthy (%s); restarting %s", state["error"], state["mode"])
                await _restart()


async def ensure_healthy() -> bool:
    """Gate for starting a voice agent: tools must be reachable from the internet right now."""
    async with _lock:
        for _ in range(5 if _ngrok_alive() else 2):
            if await probe(str(state.get("url") or "")):
                await _record(True)
                return True
            await asyncio.sleep(2)
        await _record(False)
        return await _restart()


async def _drain(stream: asyncio.StreamReader) -> None:
    while await stream.readline():
        pass


async def stop() -> None:
    if _proc and _proc.returncode is None:
        _proc.terminate()
