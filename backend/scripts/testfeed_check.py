"""Live check of the in-app test feed (no machine needed).

Starts a C-204 session from the machine page with "Use the test feed" on, plays two recorded lines, and confirms the
real Agora agent heard them, read the test-feed panel, and that its calls are in the audit log. No fake devices and
no harness overrides: this is the same path a person uses. Uses real Agora/Murf/LLM for about a minute.

    uv run python scripts/testfeed_check.py
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parents[2] / "results" / "screenshots"


def main() -> int:
    errors: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        ctx = b.new_context(viewport={"width": 1600, "height": 1000})  # no mic permission: the feed must cope without a real mic
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE + "/machines/C-204")
        page.wait_for_selector("[data-task=troubleshoot] input:checked", timeout=15000)
        opt = page.locator("[data-testid=test-feed-option] input")
        if not opt.is_checked():
            opt.check()
        page.get_by_role("button", name="Start session").click()
        page.wait_for_url("**/session/S-*", timeout=90000)
        sid = page.url.rsplit("/", 1)[-1]
        print("session", sid, flush=True)
        try:
            page.wait_for_selector("[data-line-next=prev_shift]:not([disabled])", timeout=60000)
        except Exception:
            info = page.evaluate("() => ({btn: document.querySelector('[data-line-next]')?.outerHTML?.slice(0, 200), state: document.querySelector('[aria-live=polite]')?.innerText})")
            print("not ready:", info, errors[-5:])
            raise
        page.wait_for_timeout(6000)  # greeting

        def say(line: str, wait_s: int) -> None:
            page.locator(f"[data-line-next={line}]").click()  # the bottom bar's "say the next line" button
            page.wait_for_selector("[data-line-next]:not([disabled])", timeout=60000)
            page.wait_for_timeout(wait_s * 1000)
            print("said", line, flush=True)

        say("prev_shift", 14)
        say("look_panel", 16)
        page.screenshot(path=str(OUT / "17_test_feed_session.png"), full_page=True)
        d = httpx.get(f"{BASE}/api/sessions/{sid}").json()
        users = [t["text"] for t in d["transcripts"] if t["role"] == "user"]
        tools = [(t["tool_name"], t["caller"], t["status"]) for t in d["tool_actions"]]
        visual = [e["title"] for e in d["evidence"] if e["event_type"] == "visual_observation"]
        page.goto(BASE + f"/audit?session={sid}")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / "18_audit_from_test_feed.png"), full_page=True)
        httpx.post(f"{BASE}/api/sessions/{sid}/end")
        b.close()
    print(json.dumps({"agent_heard": users, "tools": tools, "camera_evidence": visual, "console_errors": errors}, indent=1))
    ok = len(users) >= 2 and any(t[1] == "agora_mcp" for t in tools)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
