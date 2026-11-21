"""Configurable use cases: data packs (machines/sites) and task profiles (what the session is for)."""
import re

import pytest
from fastapi.testclient import TestClient

from app import packs, tools
from app import services as svc
from app.agora_session import agora_sessions, build_instructions
from app.api import create_app
from app.config import settings
from app.db import connect, tx, utcnow
from app.mcp_server import CORE_TOOLS, TOOL_NAMES


def _session(sid: str, asset: str, task: str) -> str:
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status, task_id) VALUES (?,?,?,?,?,?,?)",
                     (sid, asset, "Kavya Rao", "A shift", utcnow(), "ACTIVE", task))
    return sid


def test_all_packs_load_with_their_machines_and_manuals():
    conn = connect()
    try:
        ids = {a["asset_id"] for a in svc.list_assets(conn)}
        assert {"C-204", "P-117", "CV-310", "AHU-3"} <= ids
        models = {r[0] for r in conn.execute("SELECT DISTINCT asset_model FROM manual_chunks")}
        assert {"KS-75", "TL-600", "NB-AH20"} <= models
        # each asset knows which pack it came from
        assert svc.get_asset(conn, "CV-310")["metadata"]["pack"] == "packaging_line"
    finally:
        conn.close()


def test_pack_integrity_references_resolve():
    """Every pack's references must point at real records, so a new pack can't silently break the agent."""
    conn = connect()
    try:
        assets = {r[0] for r in conn.execute("SELECT asset_id FROM assets")}
        parts = {r[0] for r in conn.execute("SELECT part_id FROM parts")}
        for (a,) in conn.execute("SELECT asset_id FROM work_orders UNION SELECT asset_id FROM evidence UNION SELECT asset_id FROM handoffs"):
            assert a in assets
        for chunk_id, body in conn.execute("SELECT chunk_id, body FROM manual_chunks"):
            for ref in re.findall(r"\(part ([A-Z0-9-]+)\)|part ([A-Z0-9-]{4,})", body):
                pid = next(x for x in ref if x)
                assert pid in parts, f"{chunk_id} mentions unknown part {pid}"
        for pid in packs.available_pack_ids():
            for a in packs.read_pack(pid)["assets"]:
                for t in a["metadata"].get("tasks", []):
                    packs.get_task(t)  # raises on unknown task id
    finally:
        conn.close()


@pytest.mark.parametrize("asset,query,section", [
    ("CV-310", "monthly preventive maintenance checklist", "4.1"),
    ("CV-310", "F-12 overload trip causes", "2.1"),
    ("AHU-3", "inspection round readings and limits", "3.1"),
    ("AHU-3", "fan belt squeal tension", "4.1"),
    ("C-204", "quarterly preventive maintenance checklist", "8.2"),
])
def test_manual_search_works_per_machine(asset, query, section):
    import asyncio

    sid = _session("S-1001", asset, "troubleshoot")
    out = asyncio.run(tools.search_maintenance_manual(svc.SessionContext(sid, asset, "Kavya Rao"), query, None))
    assert out["sections"][0]["section"] == section


def test_tasks_offered_per_asset_with_defaults():
    conn = connect()
    try:
        assert packs.default_task_id(svc.get_asset(conn, "C-204")) == "troubleshoot"
        assert packs.default_task_id(svc.get_asset(conn, "CV-310")) == "preventive_maintenance"
        assert packs.default_task_id(svc.get_asset(conn, "AHU-3")) == "inspection_round"
        assert {t["id"] for t in packs.tasks_for_asset(svc.get_asset(conn, "AHU-3"))} == {
            "inspection_round", "preventive_maintenance", "troubleshoot", "onboarding", "shift_briefing"}
    finally:
        conn.close()


def test_prompt_and_agent_config_follow_task_and_machine(monkeypatch):
    monkeypatch.setattr(settings, "agora_app_id", "0123456789abcdef0123456789abcdef")
    monkeypatch.setattr(settings, "agora_app_certificate", "fedcba9876543210fedcba9876543210")
    monkeypatch.setattr(settings, "murf_api_key", "murf-secret-value")
    monkeypatch.setattr(settings, "mcp_public_url", "https://example.ngrok.app")
    conn = connect()
    asset = svc.get_asset(conn, "CV-310")
    conn.close()

    pm = packs.get_task("preventive_maintenance")
    text = build_instructions(asset, "Kavya Rao", "A shift", pm)
    assert "Preventive maintenance" in text and "one step at a time" in text
    assert "MCC-2" in text and "C-204" not in text and "bearing or coupling" not in text  # this machine's safety, not the compressor's

    brief = packs.get_task("shift_briefing")
    agent = agora_sessions.build_agent("S-1001", asset, "Kavya Rao", "A shift", brief)
    session = agent.create_async_session(channel="st-test", agent_uid="12345678", remote_uids=["4321"],
                                         idle_timeout=120, enable_string_uid=False, expires_in=3600)
    p = agora_sessions.redacted_properties(agora_sessions.request_preview(session))
    allowed = p["llm"]["mcp_servers"][0]["allowed_tools"]
    assert sorted(allowed) == sorted(brief["tools"]) and "update_work_order" not in allowed
    assert "shift briefing" in p["llm"]["greeting_message"] and "Case conveyor CV-310" in p["llm"]["greeting_message"]

    # default task gets the core tool set (domain tools are opt-in)
    agent = agora_sessions.build_agent("S-1001", asset, "Kavya Rao", "A shift", pm)
    session = agent.create_async_session(channel="st-test", agent_uid="12345678", remote_uids=["4321"],
                                         idle_timeout=120, enable_string_uid=False, expires_in=3600)
    p = agora_sessions.redacted_properties(agora_sessions.request_preview(session))
    assert sorted(p["llm"]["mcp_servers"][0]["allowed_tools"]) == sorted(CORE_TOOLS)


def test_task_tool_allowlist_is_enforced_server_side():
    import asyncio

    sid = _session("S-1001", "CV-310", "shift_briefing")
    r = asyncio.run(tools.run_tool("update_work_order", {}, sid, "agora_mcp",
                                   lambda c: tools.update_work_order(c, "WO-2214", "WAITING_PARTS", "x")))
    assert r["ok"] is False and r["error"] == "not_available_in_task"
    conn = connect()
    try:
        assert conn.execute("SELECT status FROM work_orders WHERE work_order_id='WO-2214'").fetchone()[0] == "IN_PROGRESS"
    finally:
        conn.close()
    # reads still work in the briefing session
    r = asyncio.run(tools.run_tool("get_previous_handoff", {}, sid, "agora_mcp", lambda c: tools.get_previous_handoff(c, None)))
    assert r["ok"] and r["handoff_id"] == "H-0039"


def test_handoff_records_the_task():
    import asyncio

    sid = _session("S-1001", "AHU-3", "inspection_round")
    asyncio.run(tools.run_tool("record_observation", {}, sid, "agora_mcp",
                               lambda c: tools.record_observation(c, "technician_report", "Bag filter 262 Pa", None)))
    h = asyncio.run(tools.run_tool("create_shift_handoff", {}, sid, "agora_mcp", lambda c: tools.create_shift_handoff(c)))
    assert h["verified"]
    conn = connect()
    try:
        rep = svc.row_to_dict(conn.execute("SELECT * FROM handoffs WHERE handoff_id=?", (h["handoff_id"],)).fetchone())["report"]
    finally:
        conn.close()
    assert rep["task"] == {"id": "inspection_round", "label": "Inspection round"}
    assert "Inspection round" in rep["spoken_summary"]


def test_api_lists_packs_tasks_and_validates_task_choice():
    c = TestClient(create_app())
    assert {p["id"] for p in c.get("/api/packs").json()} >= {"compressor_house", "packaging_line", "building_hvac"}
    t = c.get("/api/tasks", params={"asset_id": "AHU-3"}).json()
    assert t["default"] == "inspection_round" and t["tasks"][0]["id"] == "inspection_round"
    bad = c.post("/api/sessions", json={"asset_id": "CV-310", "technician": "Kavya Rao", "voice": False, "task_id": "nope"})
    assert bad.status_code == 400
    ok = c.post("/api/sessions", json={"asset_id": "CV-310", "technician": "Kavya Rao", "voice": False}).json()
    assert ok["task_id"] == "preventive_maintenance"
    d = c.get(f"/api/sessions/{ok['session_id']}").json()
    assert d["task"]["label"] == "Preventive maintenance"


def test_pack_selection_env(monkeypatch):
    monkeypatch.setenv("SHIFTTRACE_PACKS", "building_hvac")
    assert packs.selected_pack_ids() == ["building_hvac"]
    monkeypatch.setenv("SHIFTTRACE_PACKS", "building_hvac,nope")
    with pytest.raises(packs.PackError):
        packs.selected_pack_ids()


@pytest.mark.parametrize("asset,reading,value,unit,status", [
    ("AHU-3", "fan motor current", 12.4, "amps", "normal"),          # the LLM called this 'above normal' live
    ("AHU-3", "bag filter differential pressure", 262, "Pa", "out_of_limit"),
    ("AHU-3", "pre filter pressure", 120, "pascal", "outside_normal"),
    ("CV-310", "motor current", 11.8, "A", "outside_normal"),
    ("CV-310", "motor current", 12.5, "A", "out_of_limit"),
    ("C-204", "drive end vibration", 7.4, "mm/s", "out_of_limit"),
    ("C-204", "discharge temperature", 96, "C", "normal"),
    ("C-204", "discharge temperature", 96, "bar", "unit_mismatch"),
    ("C-204", "oil colour", 3, "", "no_limit_configured"),
])
def test_reading_evaluation_is_deterministic(asset, reading, value, unit, status):
    conn = connect()
    try:
        assert svc.evaluate_reading(svc.get_asset(conn, asset), reading, value, unit)["status"] == status
    finally:
        conn.close()


def test_record_reading_logs_out_of_limit_for_follow_up():
    import asyncio

    sid = _session("S-1001", "AHU-3", "inspection_round")
    r = asyncio.run(tools.run_tool("record_reading", {}, sid, "agora_mcp",
                                   lambda c: tools.record_reading(c, "filter pressure", 262, "Pa", "camera")))
    assert r["ok"] and r["verified"] and r["evaluation"] == "out_of_limit" and r["follow_up_logged"]
    assert "250" in r["say"] and "3.1" in r["say"]
    conn = connect()
    try:
        ev = conn.execute("SELECT source_type, event_type FROM evidence WHERE id=?", (r["event_id"],)).fetchone()
        loop = conn.execute("SELECT status, related_id FROM evidence WHERE id=?", (r["follow_up_logged"],)).fetchone()
    finally:
        conn.close()
    assert tuple(ev) == ("camera_model", "visual_observation") and tuple(loop) == ("open", r["event_id"])


def test_restricted_task_prompt_never_offers_unavailable_actions():
    """Live run: in a briefing session the agent offered to 'draft a procurement request' it had no tool for."""
    conn = connect()
    asset = svc.get_asset(conn, "CV-310")
    conn.close()
    brief = build_instructions(asset, "Dev Malhotra", "B shift", packs.get_task("shift_briefing"))
    assert "create_procurement_request" not in brief and "approve_procurement_request" not in brief
    assert "Never offer to do it" in brief
    full = build_instructions(asset, "Dev Malhotra", "B shift", packs.get_task("troubleshoot"))
    assert "create_procurement_request only drafts it" in full


def test_dedupe_state_is_dropped_when_session_ids_are_reused():
    """Session IDs restart at S-1001 after a reset; stale keys made capture skip every vision step live."""
    from app import capture, guard

    capture._scheduled.add(("S-1001", "3"))
    guard._flagged.add(("S-1001", "3", "recorded"))
    c = TestClient(create_app())
    c.post("/api/sessions", json={"asset_id": "C-204", "technician": "Kavya Rao", "voice": False})
    assert ("S-1001", "3") not in capture._scheduled and ("S-1001", "3", "recorded") not in guard._flagged
