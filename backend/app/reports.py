"""Shareable reports: a self-contained HTML handoff report, Excel workbooks, and links back to the console.

Reports are attached as files to messages (Telegram, WhatsApp), so they can be read by someone who cannot reach this
console (the console itself is local-only by design). Links point at PUBLIC_CONSOLE_URL (default http://localhost:8000).
"""
from __future__ import annotations

import html
import io
import json
import os
from typing import Any
from urllib.parse import quote, urlencode

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .db import connect, rows_to_dicts


def console_url() -> str:
    return (os.getenv("PUBLIC_CONSOLE_URL", "").strip() or "http://localhost:8000").rstrip("/")


def links_for(asset_id: str | None, session_id: str | None, ref: str | None = None, event_type: str | None = None) -> dict[str, str]:
    base = console_url()
    out = {}
    if ref and ref.startswith("H-"):
        out["handoff"] = f"{base}/handoffs/{ref}"
        out["handoff_excel"] = f"{base}/api/handoffs/{ref}/report.xlsx"
    if session_id:
        out["session"] = f"{base}/session/{session_id}"
        out["audit"] = f"{base}/audit?session={quote(session_id)}"
    if asset_id and asset_id not in ("console",):
        out["machine"] = f"{base}/machines/{asset_id}"
    out["operations_excel"] = f"{base}/api/reports/operations.xlsx"
    return out


def calendar_links(title: str, due_date: str | None, details: str = "") -> dict[str, str]:
    """'Add to calendar' links that work for anyone, with no account connection (all-day event on the due date)."""
    if not due_date:
        return {}
    d = due_date.replace("-", "")
    nxt = _next_day(due_date)
    g = "https://calendar.google.com/calendar/render?" + urlencode({"action": "TEMPLATE", "text": title, "dates": f"{d}/{nxt}", "details": details})
    o = "https://outlook.live.com/calendar/0/deeplink/compose?" + urlencode({"subject": title, "startdt": due_date, "enddt": due_date, "allday": "true", "body": details})
    return {"google_calendar": g, "outlook_calendar": o}


def _next_day(iso: str) -> str:
    from datetime import date, timedelta
    y, m, dd = (int(x) for x in iso[:10].split("-"))
    return (date(y, m, dd) + timedelta(days=1)).strftime("%Y%m%d")


# --------------------------------------------------------------------------- handoff report

def _handoff(handoff_id: str) -> dict[str, Any] | None:
    conn = connect()
    try:
        rows = rows_to_dicts(conn.execute("SELECT * FROM handoffs WHERE handoff_id=?", (handoff_id,)).fetchall())
    finally:
        conn.close()
    return rows[0] if rows else None


def handoff_html(handoff_id: str) -> str | None:
    h = _handoff(handoff_id)
    if not h:
        return None
    r = h["report"]
    e = html.escape
    def items(xs: list[dict[str, Any]], key: str = "text") -> str:
        return "".join(f"<li>{e(str(x.get(key, '')))}{'<br><small>' + e(str(x['detail'])) + '</small>' if x.get('detail') else ''}</li>" for x in xs) or "<li class=muted>None</li>"
    links = links_for(r["asset"]["asset_id"], r["session"].get("session_id"), handoff_id)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Shift handoff {e(handoff_id)} · {e(r['asset']['name'])}</title>
<style>body{{font:15px/1.5 system-ui,Segoe UI,sans-serif;max-width:760px;margin:24px auto;padding:0 16px;color:#16202a}}h1{{font-size:26px;margin:.2em 0}}
h2{{font-size:16px;margin:1.4em 0 .4em;border-top:2px solid #16202a;padding-top:.5em}}.muted,small{{color:#66717b}}.head{{font-size:19px}}
.open li::marker{{content:"◆ ";color:#a26400}}.done li::marker{{content:"✓ ";color:#1f7a5c}}.fail li::marker{{content:"▲ ";color:#b3261e}}
blockquote{{border-left:4px solid #16202a;margin:0;padding-left:12px;color:#3f4a54}}a{{color:#1d4f8f}}footer{{margin-top:2em;font-size:12px;color:#66717b}}</style></head><body>
<div class=muted>Shift handoff {e(handoff_id)} · filed {e(h['created_at'])}</div>
<h1>{e(r['asset']['name'])}</h1>
<div class=muted>From {e(r['session']['technician'])}, {e(r['session']['shift'])}{', ' + e(r['task']['label']) if r.get('task') else ''} · {e(r['asset']['location'])}</div>
<p class=head>{e(r['headline'])}</p>
<h2>Still open ({len(r['open_loops'])})</h2><ul class=open>{items(r['open_loops'])}</ul>
<h2>Not done ({len(r['actions_failed_or_pending'])})</h2><ul class=fail>{items(r['actions_failed_or_pending'])}</ul>
<h2>Done and verified ({len(r['actions_completed'])})</h2><ul class=done>{items(r['actions_completed'])}</ul>
<h2>Seen and said ({len(r['observations'])})</h2><ul>{"".join(f"<li>{e(o['text'])} <small>({e(o['source'])})</small></li>" for o in r['observations']) or "<li class=muted>None</li>"}</ul>
<h2>Follow-ups</h2><ul>{"".join(f"<li>{e(f['title'])} <small>{e(f['follow_up_id'])}, {e(str(f.get('assignee')))}, due {e(str(f.get('due')))}</small></li>" for f in r.get('follow_ups') or []) or "<li class=muted>None</li>"}</ul>
<h2>Suggested next steps</h2><ol>{"".join(f"<li>{e(s)}</li>" for s in r['suggested_next_steps'])}</ol>
<h2>Spoken summary</h2><blockquote>{e(r['spoken_summary'])}</blockquote>
<footer>Written by {e(r['generated_by'])}. Every line maps to a stored record. Console: <a href="{e(links.get('handoff', ''))}">{e(links.get('handoff', ''))}</a> · Synthetic demo data.</footer>
</body></html>"""


# --------------------------------------------------------------------------- Excel

HEAD = PatternFill("solid", fgColor="16202A")


def _sheet(wb: Workbook, title: str, cols: list[str], rows: list[list[Any]], link_cols: dict[int, int] | None = None) -> None:
    ws = wb.create_sheet(title[:31])
    ws.append(cols)
    for c in ws[1]:
        c.font, c.fill, c.alignment = Font(bold=True, color="FFFFFF"), HEAD, Alignment(vertical="center")
    for row in rows:
        ws.append([json.dumps(v) if isinstance(v, (dict, list)) else v for v in row])
    for idx, _ in (link_cols or {}).items():  # make URL cells clickable
        for r in range(2, ws.max_row + 1):
            cell = ws.cell(row=r, column=idx)
            if isinstance(cell.value, str) and cell.value.startswith("http"):
                cell.hyperlink, cell.style = cell.value, "Hyperlink"
    for i, col in enumerate(cols, 1):
        width = max([len(str(col))] + [min(60, len(str(ws.cell(row=r, column=i).value or ""))) for r in range(2, ws.max_row + 1)])
        ws.column_dimensions[get_column_letter(i)].width = max(10, min(60, width + 2))
    ws.freeze_panes = "A2"


def _q(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    conn = connect()
    try:
        return rows_to_dicts(conn.execute(sql, params).fetchall())
    finally:
        conn.close()


def handoff_xlsx(handoff_id: str) -> bytes | None:
    h = _handoff(handoff_id)
    if not h:
        return None
    r = h["report"]
    links = links_for(r["asset"]["asset_id"], r["session"].get("session_id"), handoff_id)
    wb = Workbook()
    wb.remove(wb.active)
    _sheet(wb, "Summary", ["Field", "Value"], [["Handoff", handoff_id], ["Machine", f"{r['asset']['asset_id']} {r['asset']['name']}"], ["From", f"{r['session']['technician']}, {r['session']['shift']}"],
                                               ["Filed", h["created_at"]], ["Headline", r["headline"]], ["Spoken summary", r["spoken_summary"]],
                                               ["Report (console)", links.get("handoff")], ["Session audit log", links.get("audit")]], {2: 2})
    _sheet(wb, "Still open", ["Item", "Type", "Raised by"], [[x["text"], x.get("type"), x.get("raised_by")] for x in r["open_loops"]])
    _sheet(wb, "Done and verified", ["Action", "Detail", "Ref"], [[x["text"], x.get("detail"), x.get("ref")] for x in r["actions_completed"]])
    _sheet(wb, "Not done", ["Item", "Detail", "Status"], [[x["text"], x.get("detail"), x.get("status")] for x in r["actions_failed_or_pending"]])
    _sheet(wb, "Seen and said", ["Observation", "Source", "Time"], [[x["text"], x["source"], x.get("ts")] for x in r["observations"]])
    _sheet(wb, "Follow-ups", ["Follow-up", "Title", "Assignee", "Due"], [[x["follow_up_id"], x["title"], x.get("assignee"), x.get("due")] for x in r.get("follow_ups") or []])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def operations_xlsx() -> bytes:
    """Everything a supervisor exports: sessions with report links, actions, orders, transfers, follow-ups, training, events."""
    base = console_url()
    wb = Workbook()
    wb.remove(wb.active)
    hand = {h["session_id"]: h["handoff_id"] for h in _q("SELECT handoff_id, session_id FROM handoffs")}
    _sheet(wb, "Sessions", ["Session", "Machine", "Technician", "Shift", "Task", "Started", "Ended", "Status", "Summary", "Handoff report", "Audit log"],
           [[s["session_id"], s["asset_id"], s["technician"], s["shift_label"], s.get("task_id"), s["started_at"], s["ended_at"], s["status"], s["summary"],
             f"{base}/handoffs/{hand[s['session_id']]}" if s["session_id"] in hand else None, f"{base}/audit?session={s['session_id']}"]
            for s in _q("SELECT * FROM sessions ORDER BY started_at DESC")], {10: 10, 11: 11})
    _sheet(wb, "Tool calls (audit)", ["Time", "Session", "Tool", "Made by", "Status", "Verified", "Input", "Result message"],
           [[t["ts"], t["session_id"], t["tool_name"], t["caller"], t["status"], (t.get("result") or {}).get("verified") if isinstance(t.get("result"), dict) else None,
             t.get("input"), (t.get("result") or {}).get("message") if isinstance(t.get("result"), dict) else None]
            for t in _q("SELECT * FROM tool_actions ORDER BY id DESC LIMIT 2000")])
    _sheet(wb, "Orders", ["Request", "Part", "Qty", "Work order", "Status", "Approved by", "Via", "Supplier", "Supplier ref", "Expected", "Failure"],
           [[p["request_id"], p["part_id"], p["quantity"], p["work_order_id"], p["status"], p["approved_by"], p["approval_via"], p["supplier"], p["supplier_ref"], p["expected_by"], p["failure_reason"]]
            for p in _q("SELECT * FROM procurement_requests ORDER BY created_at DESC")])
    _sheet(wb, "Stock transfers", ["Transfer", "Part", "Qty", "From", "To", "Status", "Confirmed by", "Via", "ERP ref", "Created"],
           [[t["transfer_id"], t["part_id"], t["quantity"], t["from_location"], t["to_location"], t["status"], t["confirmed_by"], t["confirmation_via"], t["erp_ref"], t["created_at"]]
            for t in _q("SELECT * FROM stock_transfers ORDER BY created_at DESC")])
    _sheet(wb, "Stock by location", ["Part", "Name", "Location", "Quantity"],
           [[r["part_id"], r["name"], r["location"], r["quantity"]] for r in _q("SELECT s.part_id, p.name, s.location, s.quantity FROM stock_levels s JOIN parts p ON p.part_id=s.part_id ORDER BY s.part_id")])
    _sheet(wb, "Follow-ups", ["Follow-up", "Title", "Due", "Assignee", "Machine", "Status", "Add to Google Calendar"],
           [[f["follow_up_id"], f["title"], f["due_date"] or f["due_text"], f["assignee"], f["asset_id"], f["status"],
             calendar_links(f["title"], f["due_date"]).get("google_calendar")] for f in _q("SELECT * FROM follow_ups ORDER BY created_at DESC")], {7: 7})
    _sheet(wb, "Learning records", ["Trainee", "Module", "Title", "Status", "Score", "Attempts", "Updated"],
           [[x["trainee"], x["module_id"], x["title"], x["status"], x["score"], x["attempts"], x["updated_at"]] for x in _q("SELECT * FROM learning_records ORDER BY updated_at DESC")])
    _sheet(wb, "Integration events", ["Time", "Event", "Ref", "Machine", "Summary"],
           [[e["ts"], e["event_type"], e["ref"], e["asset_id"], e["summary"]] for e in _q("SELECT * FROM integration_events ORDER BY id DESC")])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
