"""Live check of the cost controls: idle pause stops the agent and leaves the call, Resume brings a fresh agent back,
and the session's cost meter stops while paused. Uses real Agora for about three minutes.

    uv run python scripts/pause_check.py
"""
from __future__ import annotations

import json
import time

import httpx
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"


def main() -> int:
    c = httpx.Client(base_url=BASE, timeout=90)
    c.post("/api/demo/reset")
    before = c.get("/api/site-settings").json()
    c.post("/api/site-settings", json={"idle_pause_min": 1})
    out: dict = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel="msedge", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
            page = b.new_context(viewport={"width": 1600, "height": 1000}).new_page()
            page.goto(f"{BASE}/machines/C-204")
            page.wait_for_selector("[data-task=troubleshoot] input:checked", timeout=15000)
            page.get_by_role("button", name="Start session").click()
            page.wait_for_url("**/session/S-*", timeout=90000)
            sid = page.url.rsplit("/", 1)[-1]
            page.wait_for_selector("[data-line-next]:not([disabled])", timeout=60000)
            t0 = time.time()
            page.wait_for_selector("text=Voice paused to save cost", timeout=150000)  # 1 min idle after the greeting
            out["paused_after_s"] = round(time.time() - t0)
            out["agent_running_after_pause"] = sid in c.get("/api/health").json()["active_agents"]
            cost1 = c.get(f"/api/sessions/{sid}/cost").json()
            time.sleep(20)
            cost2 = c.get(f"/api/sessions/{sid}/cost").json()
            out["meter_stopped_while_paused"] = cost2["voice_minutes"] == cost1["voice_minutes"] and cost2["paused_now"]
            page.get_by_role("button", name="Resume voice").first.click()
            page.wait_for_selector("[data-line-next]:not([disabled])", timeout=90000)
            out["resumed"] = sid in c.get("/api/health").json()["active_agents"]
            ev = [e["title"] for e in c.get(f"/api/sessions/{sid}").json()["evidence"]]
            out["evidence"] = [t for t in ev if "paused" in t or "restarted" in t.lower()]
            out["cost"] = c.get(f"/api/sessions/{sid}/cost").json()["total_usd"]
            c.post(f"/api/sessions/{sid}/end")
            b.close()
    finally:
        c.post("/api/site-settings", json={"idle_pause_min": before.get("idle_pause_min", "3")})
    print(json.dumps(out, indent=1))
    ok = bool(out.get("paused_after_s")) and not out.get("agent_running_after_pause") and out.get("meter_stopped_while_paused") and out.get("resumed")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
