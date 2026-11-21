"""Live check of the non-maintenance workflows through the real Agora agent and the in-app test feed (no machine).

  warehouse: DC2-ZB, warehouse_ops. Ask about stock, ask to move 20 cases from reserve to the pick face, say yes
             after the read-back. Expect transfer DONE, stock moved, ERP posted, all by the voice agent.
  training:  C-204, onboarding. Start training, answer three questions (correct, partly, wrong), finish.
             Expect a learning record NEEDS_REVIEW (about 50%).

    uv run python scripts/workflows_check.py [warehouse|training]
Uses real Agora/Murf/LLM for a few minutes.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import Page, sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parents[2] / "results" / "screenshots"


def run_session(page: Page, asset: str, task: str) -> str:
    page.goto(f"{BASE}/machines/{asset}")
    page.wait_for_selector(f"[data-task={task}]", timeout=15000)
    page.locator(f"[data-task={task}]").click()
    opt = page.locator("[data-testid=test-feed-option] input")
    if not opt.is_checked():
        opt.check()
    page.get_by_role("button", name="Start session").click()
    page.wait_for_url("**/session/S-*", timeout=90000)
    sid = page.url.rsplit("/", 1)[-1]
    page.wait_for_selector("[data-line-next]:not([disabled])", timeout=60000)
    page.wait_for_timeout(7000)  # greeting
    return sid


def say_line(page: Page, line: str, settle_s: float) -> None:
    """Pick a specific line from the full list (the bottom bar's list), then wait for the agent's turn."""
    page.locator("button[title='All test lines']").click()
    page.locator(f"[data-line={line}]").click()
    page.wait_for_selector("[data-line-next]:not([disabled])", timeout=90000)
    page.wait_for_timeout(int(settle_s * 1000))
    print("  said", line, flush=True)


def detail(sid: str) -> dict:
    return httpx.get(f"{BASE}/api/sessions/{sid}", timeout=30).json()


def warehouse(page: Page) -> dict:
    sid = run_session(page, "DC2-ZB", "warehouse_ops")
    say_line(page, "wh_stock", 12)
    say_line(page, "wh_move", 16)
    say_line(page, "wh_yes", 16)
    d = detail(sid)
    if not any(t["status"] == "DONE" for t in d.get("transfers", [])):  # the agent may need one more nudge to read back
        say_line(page, "wh_yes", 14)
        d = detail(sid)
    page.screenshot(path=str(OUT / "19_warehouse_session.png"), full_page=True)
    tools = [(t["tool_name"], t["caller"], t["status"]) for t in d["tool_actions"]]
    stock = httpx.get(f"{BASE}/api/inventory").json()
    rice = next(p for p in stock if p["part_id"] == "SKU-2231")
    httpx.post(f"{BASE}/api/sessions/{sid}/end", timeout=60)
    ok = any(t["status"] == "DONE" and t["confirmation_via"] == "voice" and t["erp_ref"] for t in d.get("transfers", []))
    return {"session": sid, "heard": [t["text"] for t in d["transcripts"] if t["role"] == "user"], "tools": tools,
            "transfers": [{k: t[k] for k in ("transfer_id", "status", "quantity", "from_location", "to_location", "erp_ref", "confirmation_via")} for t in d.get("transfers", [])],
            "rice_locations": rice["locations"], "pass": ok}


def training(page: Page) -> dict:
    sid = run_session(page, "C-204", "onboarding")
    for line, wait in (("ob_start", 14), ("ob_a1", 14), ("ob_a2", 14), ("ob_a3", 14), ("ob_finish", 16)):
        say_line(page, line, wait)
    d = detail(sid)
    page.screenshot(path=str(OUT / "20_training_session.png"), full_page=True)
    recs = httpx.get(f"{BASE}/api/learning-records").json()
    mine = [r for r in recs if r["last_session_id"] == sid]
    httpx.post(f"{BASE}/api/sessions/{sid}/end", timeout=60)
    tools = [(t["tool_name"], t["status"], (t["result"] or {}).get("result")) for t in d["tool_actions"]]
    return {"session": sid, "heard": [t["text"] for t in d["transcripts"] if t["role"] == "user"], "tools": tools,
            "learning_record": mine, "pass": bool(mine) and any(t[0] == "record_training_answer" for t in tools)}


def main(which: list[str]) -> int:
    results = {}
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        for w in which:
            httpx.post(f"{BASE}/api/demo/reset", timeout=60)
            page = b.new_context(viewport={"width": 1600, "height": 1000}).new_page()
            print(w, flush=True)
            results[w] = {"warehouse": warehouse, "training": training}[w](page)
            print(json.dumps({w: results[w]}, indent=1), flush=True)
            page.context.close()
        b.close()
    ok = all(r["pass"] for r in results.values())
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["warehouse", "training"]))
