"""Headless UI smoke test using the locally installed Microsoft Edge (Playwright channel=msedge).

    uv run python scripts/ui_smoke.py [--voice]

Visits every console page, records console errors, saves screenshots to results/screenshots/.
--voice: also starts a voice session with Chromium's fake camera/mic (needs Agora + Murf keys).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parents[2] / "results" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def main(voice: bool) -> int:
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True, args=[
            "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--autoplay-policy=no-user-gesture-required"])
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000}, permissions=["camera", "microphone"])
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(f"{page.url} {m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"{page.url} pageerror: {e}"))

        def shot(path: str, name: str, wait: str | None = None):
            page.goto(BASE + path)
            if wait:
                page.wait_for_selector(f"text={wait}", timeout=10000)
            page.wait_for_timeout(700)
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            print(f"  screenshot {name}.png  ({path})")

        shot("/", "00_landing", "Try the live demo")
        shot("/board", "01_machines", "Compressor C-204")
        shot("/machines/C-204", "02_machine_memory", "Still open")
        shot("/handoffs/H-0042", "03_previous_handoff", "Spoken summary")
        shot("/panel", "04_simulated_panel", "KESTREL KS-75")
        shot("/panel/CV-310", "04b_panel_conveyor", "TRACKLINE TL-600")
        shot("/panel/AHU-3", "04c_panel_ahu", "NORTHBREEZE NB-AH20")

        # The board leads to the machine page; starting is part of that page (no form): each machine offers its own tasks
        page.goto(BASE + "/board")
        page.locator("[data-asset=CV-310]").get_by_role("link", name="Open CV-310").click()
        page.wait_for_selector("[data-task=preventive_maintenance] input:checked", timeout=10000)
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "10_task_picker.png"))
        print("  screenshot 10_task_picker.png")
        page.locator("[data-task=shift_briefing]").click()
        page.get_by_role("checkbox", name="Start the voice agent").uncheck()
        page.get_by_role("button", name="Start session").click()
        page.wait_for_url("**/session/S-*", timeout=60000)
        page.wait_for_selector("text=Shift briefing (no changes)", timeout=10000)
        page.locator("[data-testid=task-chip] summary").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "11_task_chip_briefing.png"))
        print("  screenshot 11_task_chip_briefing.png")
        bsid = page.url.rsplit("/", 1)[-1]
        httpx.post(f"{BASE}/api/sessions/{bsid}/end")

        page.goto(BASE + "/machines/C-204")
        page.wait_for_selector("[data-task=troubleshoot] input:checked", timeout=10000)
        if not voice:
            page.get_by_role("checkbox", name="Start the voice agent").uncheck()
        page.get_by_role("button", name="Start session").click()
        page.wait_for_url("**/session/S-*", timeout=60000)
        sid = page.url.rsplit("/", 1)[-1]
        print(f"  session {sid} started (voice={voice})")
        if voice:
            page.wait_for_timeout(15000)
        # Drive the workflow through the console tool API (same tool layer Agora calls)
        c = httpx.Client(base_url=BASE, timeout=30)
        t = lambda tool, **args: c.post("/api/console/tool", json={"tool": tool, "session_id": sid, "args": args}).json()
        t("get_previous_handoff")
        t("record_observation", kind="visual", summary="TEMP HIGH lamp appears to be flashing; display reads A-17, 108 C")
        t("record_observation", kind="technician_report", summary="Vibration started before the temperature warning", detail="Technician: it shook first, then the lamp came on")
        t("search_maintenance_manual", query="A-17 recurring after sensor replacement")
        inv = t("check_inventory", part="drive end bearing")
        draft = t("create_procurement_request", part="BRG-6316-C3", quantity=1, reason="DE bearing suspected (7.4 mm/s)")
        print("  inventory:", inv.get("summary"), "| draft:", draft.get("request_id"), draft.get("status"))
        page.wait_for_selector("text=Approval required", timeout=10000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "05_live_session_approval.png"), full_page=True)
        print("  screenshot 05_live_session_approval.png")
        page.get_by_role("button", name="Approve & submit").click()
        page.wait_for_selector("[aria-label='Session trace'] >> text=submitted to supplier", timeout=10000)
        t("update_work_order", status="WAITING_PARTS", note=f"DE bearing ordered on {draft.get('request_id')}; coupling still to check")
        page.wait_for_selector("[aria-label='Session trace'] >> text=WAITING_PARTS", timeout=10000)
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "06_live_session_before_finish.png"), full_page=True)
        print("  screenshot 06_live_session_before_finish.png")
        page.emulate_media(color_scheme="dark")
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "14_live_session_dark.png"), full_page=True)
        print("  screenshot 14_live_session_dark.png")
        page.emulate_media(color_scheme="light")
        page.set_viewport_size({"width": 400, "height": 860})
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "09_mobile_session.png"), full_page=True)
        print("  screenshot 09_mobile_session.png")
        page.set_viewport_size({"width": 1600, "height": 1000})
        page.get_by_role("button", name="Finish and hand over").first.click()
        page.wait_for_url("**/handoffs/H-*", timeout=30000)
        page.wait_for_selector("text=Spoken summary", timeout=10000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "07_new_handoff.png"), full_page=True)
        print("  screenshot 07_new_handoff.png")
        detail = c.get(f"/api/sessions/{sid}").json()
        assert detail["status"] == "ENDED" and detail["handoff"], "Finish should write the handoff and end the session"
        shot("/actions", "08_action_centre", "Procurement requests")
        shot("/audit", "12_audit_log", "Audit log")
        page.locator("tbody tr:has(button)").first.click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "12b_audit_inspect.png"), full_page=True)
        print("  screenshot 12b_audit_inspect.png")
        shot("/system", "13_system", "Live checks")
        shot("/handoffs", "16_handoff_list", "Handoffs")
        shot("/integrations", "21_integrations", "Connected systems")
        shot("/quality", "22_quality", "Agent quality")
        page.get_by_role("tab", name="Dataset").click()
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "22b_quality_dataset.png"), full_page=True)
        print("  screenshot 22b_quality_dataset.png")
        page.emulate_media(color_scheme="dark")
        shot("/board", "15_machines_dark", "Compressor C-204")
        page.emulate_media(color_scheme="light")
        browser.close()
    print(json.dumps({"console_errors": errors}, indent=1))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main("--voice" in sys.argv))
