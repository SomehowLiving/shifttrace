"""Shareable reports: the handoff as a self-contained HTML page and an Excel workbook, and the operations export."""
import asyncio
import io

from openpyxl import load_workbook

from app import reports, tools
from app.db import tx, utcnow


def _handoff():
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status, task_id) VALUES (?,?,?,?,?,?,?)",
                     ("S-1001", "C-204", "Kavya Rao", "A shift", utcnow(), "ACTIVE", "troubleshoot"))
    out = asyncio.run(tools.run_tool("create_shift_handoff", {}, "S-1001", "test", lambda c: tools.create_shift_handoff(c)))
    return out["handoff_id"]


def test_handoff_report_html_is_self_contained_and_escaped(monkeypatch):
    monkeypatch.delenv("PUBLIC_CONSOLE_URL", raising=False)
    hid = _handoff()
    page = reports.handoff_html(hid)
    assert page.startswith("<!doctype html>") and hid in page and "<script" not in page and "http://localhost:8000/handoffs/" + hid in page
    assert reports.handoff_html("H-0") is None


def test_handoff_excel_has_a_sheet_per_section_with_links():
    hid = _handoff()
    wb = load_workbook(io.BytesIO(reports.handoff_xlsx(hid)))
    assert wb.sheetnames == ["Summary", "Still open", "Done and verified", "Not done", "Seen and said", "Follow-ups"]
    summary = {r[0].value: r[1] for r in wb["Summary"].iter_rows(min_row=2)}
    assert summary["Handoff"].value == hid and summary["Report (console)"].hyperlink.target.endswith(f"/handoffs/{hid}")


def test_operations_workbook_links_each_session_to_its_handoff_and_audit_log():
    hid = _handoff()
    wb = load_workbook(io.BytesIO(reports.operations_xlsx()))
    for name in ("Sessions", "Tool calls (audit)", "Orders", "Stock transfers", "Follow-ups", "Learning records", "Integration events"):
        assert name in wb.sheetnames
    rows = list(wb["Sessions"].iter_rows(min_row=2))
    s = next(r for r in rows if r[0].value == "S-1001")
    assert s[9].value.endswith(f"/handoffs/{hid}") and s[9].hyperlink is not None and "audit?session=S-1001" in s[10].value


def test_calendar_links_are_all_day_on_the_due_date():
    ls = reports.calendar_links("Recount", "2026-11-30", "x")
    assert "dates=20261130%2F20261201" in ls["google_calendar"] and "startdt=2026-11-30" in ls["outlook_calendar"]
    assert reports.calendar_links("Recount", None) == {}
