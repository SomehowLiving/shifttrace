"""Real-world integrations: every verified action becomes a business event, delivered to the systems a site uses.

Connectors (each off until its environment variables are set in backend/.env):
  webhook  WEBHOOK_URL (+ WEBHOOK_SECRET)   any HTTPS endpoint: Zapier, Make, n8n, Power Automate, ERP/CMMS middleware.
                                            Body is JSON; X-Shifttrace-Signature: sha256=<HMAC of the body> when a secret is set.
  slack    SLACK_WEBHOOK_URL                Slack incoming webhook: a readable message per event.
  teams    TEAMS_WEBHOOK_URL                Microsoft Teams incoming webhook / Workflows URL.
  jira     JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY   creates an issue for escalations and follow-ups.
  github   GITHUB_TOKEN, GITHUB_REPO (owner/name)                        creates an issue for escalations and follow-ups.
  telegram TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID                         message with links per event; the handoff report (HTML +
                                                                       Excel) is attached as files when a handoff is published.
  whatsapp WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_TO         WhatsApp Cloud API (Meta). Text with links; the handoff
           (+ WHATSAPP_TEMPLATE, WHATSAPP_TEMPLATE_LANG)                 Excel report is attached as a document. Outside a 24-hour
                                                                       customer window WhatsApp only allows approved templates:
                                                                       set WHATSAPP_TEMPLATE (one body parameter) for that case.
  excel    SPREADSHEET_WEBHOOK_URL          one flat row per event, for a Power Automate flow ("When an HTTP request is
                                            received" -> "Add a row into a table" in Excel Online) or a Google Apps Script
                                            web app that appends to Google Sheets. Rows carry the report and audit links.
  local    the console's own test receiver (POST /api/integrations/receiver), switched on in Setup > Integrations.
           It verifies the signature like a real receiver would; it is labelled as a local test, not an external system.

Every message carries links back to the record (handoff report, audit log, machine, and Google/Outlook "add to
calendar" links for follow-ups), built from PUBLIC_CONSOLE_URL. The console is local-only by design, so where a channel
accepts files the report itself is attached.

Only events from successful, re-read actions are emitted. Payloads carry the business record (synthetic demo data),
never credentials. Deliveries are logged with status and retried up to three times.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
from typing import Any

import httpx

from .config import settings
from .db import connect, flag_enabled, rows_to_dicts, tx, utcnow

log = logging.getLogger("shifttrace.integrations")

EVENT_TITLES = {
    "order.submitted": "Order submitted", "transfer.posted": "Stock transfer posted to ERP", "work_order.updated": "Work order updated",
    "escalation.raised": "Escalation raised", "follow_up.scheduled": "Follow-up scheduled", "handoff.published": "Shift handoff published",
    "training.recorded": "Learning record updated", "reading.out_of_limit": "Reading out of limit", "integration.test": "Test event",
}
TICKET_EVENTS = {"escalation.raised", "follow_up.scheduled"}


def _env(k: str) -> str:
    return os.getenv(k, "").strip()


# --------------------------------------------------------------------------- events from tool results

def event_for(tool: str, args: dict[str, Any], result: dict[str, Any], session_id: str | None, asset_id: str) -> dict[str, Any] | None:
    """Map a successful, verified tool result to a business event (or None)."""
    r = result or {}
    if tool in ("approve_procurement_request", "console_approve_procurement"):
        req = r.get("request") or r
        if (req.get("status") or r.get("status")) != "SUBMITTED" or r.get("duplicate"):
            return None
        rid = req.get("request_id") or r.get("request_id")
        return _ev("order.submitted", rid, f"Order {rid} submitted to {req.get('supplier') or r.get('supplier')}, expected {req.get('expected_by') or r.get('expected_by')}",
                   {k: req.get(k, r.get(k)) for k in ("request_id", "part_id", "quantity", "work_order_id", "supplier", "supplier_ref", "expected_by", "approved_by", "approval_via")},
                   session_id, asset_id)
    if tool in ("confirm_stock_transfer", "console_confirm_transfer") and r.get("status") == "DONE" and not r.get("duplicate"):
        return _ev("transfer.posted", r.get("transfer_id"), f"Stock transfer {r.get('transfer_id')} done, ERP {r.get('erp_ref')}",
                   {"transfer_id": r.get("transfer_id"), "erp_ref": r.get("erp_ref"), "stock_now": r.get("stock_now"), "confirmed_via": r.get("confirmed_via")},
                   session_id, asset_id)
    if tool == "update_work_order":
        return _ev("work_order.updated", r.get("work_order_id"), f"{r.get('work_order_id')} is now {r.get('status')}: {args.get('note') or ''}".strip(),
                   {"work_order_id": r.get("work_order_id"), "status": r.get("status"), "note": args.get("note")}, session_id, asset_id)
    if tool == "escalate_incident" and not r.get("duplicate"):
        e = r.get("escalation") or {}
        return _ev("escalation.raised", e.get("escalation_id"), f"Escalation ({e.get('severity')}) on {asset_id}: {e.get('reason')}",
                   {k: e.get(k) for k in ("escalation_id", "work_order_id", "severity", "reason")}, session_id, asset_id)
    if tool == "schedule_follow_up" and not r.get("duplicate"):
        return _ev("follow_up.scheduled", r.get("follow_up_id"), f"{r.get('title')} (due {r.get('due')}, {r.get('assignee')})",
                   {k: r.get(k) for k in ("follow_up_id", "title", "due", "assignee")}, session_id, asset_id)
    if tool == "create_shift_handoff":
        return _ev("handoff.published", r.get("handoff_id"), r.get("headline") or "Handoff published",
                   {"handoff_id": r.get("handoff_id"), "headline": r.get("headline"), "open_loops": r.get("open_loops")}, session_id, asset_id)
    if tool == "finish_training_module":
        return _ev("training.recorded", r.get("module_id"), f"{r.get('title')}: {r.get('score')}%, {str(r.get('status')).replace('_', ' ').lower()}",
                   {k: r.get(k) for k in ("module_id", "title", "score", "status", "passed")}, session_id, asset_id)
    if tool == "record_reading" and r.get("evaluation") == "out_of_limit":
        return _ev("reading.out_of_limit", f"evidence-{r.get('event_id')}", f"{args.get('reading')}: {args.get('value')} {args.get('unit') or ''} is out of limit".strip(),
                   {"reading": args.get("reading"), "value": args.get("value"), "unit": args.get("unit"), "say": r.get("say")}, session_id, asset_id)
    return None


def _ev(kind: str, ref: Any, summary: str, payload: dict[str, Any], session_id: str | None, asset_id: str) -> dict[str, Any]:
    return {"event_type": kind, "ref": str(ref) if ref is not None else None, "summary": summary, "payload": payload,
            "session_id": session_id, "asset_id": asset_id}


def record_event(ev: dict[str, Any]) -> int:
    with tx() as conn:
        conn.execute("INSERT INTO integration_events(ts, event_type, ref, summary, payload_json, session_id, asset_id) VALUES (?,?,?,?,?,?,?)",
                     (utcnow(), ev["event_type"], ev["ref"], ev["summary"], json.dumps(ev["payload"], default=str), ev["session_id"], ev["asset_id"]))
        return int(conn.execute("SELECT max(id) FROM integration_events").fetchone()[0])


def emit(ev: dict[str, Any] | None) -> None:
    """Store the event and deliver it in the background. Never blocks or fails the tool call."""
    if not ev:
        return
    try:
        eid = record_event(ev)
    except Exception as e:  # pragma: no cover - storage problems must not break the voice turn
        log.warning("could not store integration event: %s", e)
        return
    try:
        asyncio.get_running_loop().create_task(deliver(eid))
    except RuntimeError:  # no running loop (tests / scripts): deliver synchronously
        asyncio.run(deliver(eid))


# --------------------------------------------------------------------------- connectors

def _local_on() -> bool:
    conn = connect()
    try:
        return flag_enabled(conn, "integration_local_receiver")
    finally:
        conn.close()


def connectors() -> list[dict[str, Any]]:
    """What is configured. Values are never returned, only whether each variable is set."""
    def cfg(*keys: str) -> dict[str, bool]:
        return {k: bool(_env(k)) for k in keys}
    out = [
        {"id": "webhook", "name": "Webhook (Zapier, Make, n8n, ERP middleware)", "env": cfg("WEBHOOK_URL", "WEBHOOK_SECRET"), "required": ["WEBHOOK_URL"], "events": "all"},
        {"id": "slack", "name": "Slack", "env": cfg("SLACK_WEBHOOK_URL"), "required": ["SLACK_WEBHOOK_URL"], "events": "all"},
        {"id": "teams", "name": "Microsoft Teams", "env": cfg("TEAMS_WEBHOOK_URL"), "required": ["TEAMS_WEBHOOK_URL"], "events": "all"},
        {"id": "jira", "name": "Jira (issues)", "env": cfg("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"),
         "required": ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"], "events": sorted(TICKET_EVENTS)},
        {"id": "github", "name": "GitHub Issues", "env": cfg("GITHUB_TOKEN", "GITHUB_REPO"), "required": ["GITHUB_TOKEN", "GITHUB_REPO"], "events": sorted(TICKET_EVENTS)},
        {"id": "telegram", "name": "Telegram", "env": cfg("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"), "required": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
         "events": "all", "attaches": "handoff report (HTML + Excel)"},
        {"id": "whatsapp", "name": "WhatsApp (Cloud API)", "env": cfg("WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_TO", "WHATSAPP_TEMPLATE"),
         "required": ["WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_TO"], "events": "all", "attaches": "handoff report (Excel)"},
        {"id": "excel", "name": "Excel / Google Sheets (a row per event)", "env": cfg("SPREADSHEET_WEBHOOK_URL"), "required": ["SPREADSHEET_WEBHOOK_URL"], "events": "all"},
        {"id": "local", "name": "Local test receiver (this console)", "env": {}, "required": [], "events": "all", "local": True},
    ]
    for c in out:
        c["enabled"] = _local_on() if c["id"] == "local" else all(c["env"].get(k) for k in c["required"])
    return out


def enabled_targets(event_type: str) -> list[str]:
    return [c["name"] for c in connectors() if c["enabled"] and (c["events"] == "all" or event_type in c["events"])]


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _envelope(ev: dict[str, Any]) -> dict[str, Any]:
    return {"source": "shifttrace", "event_id": ev["id"], "event_type": ev["event_type"], "title": EVENT_TITLES.get(ev["event_type"], ev["event_type"]),
            "ref": ev["ref"], "summary": ev["summary"], "asset_id": ev["asset_id"], "session_id": ev["session_id"], "ts": ev["ts"],
            "data": ev["payload"], "links": links(ev), "synthetic_demo_data": True}


LINK_LABELS = [("handoff", "Handoff report"), ("audit", "Audit log"), ("google_calendar", "Add to Google Calendar"),
               ("outlook_calendar", "Add to Outlook calendar"), ("machine", "Machine")]


def links(ev: dict[str, Any]) -> dict[str, str]:
    """Links back to the record. Follow-ups also get Google/Outlook 'add to calendar' links (no account connection needed)."""
    from . import reports
    out = reports.links_for(ev.get("asset_id"), ev.get("session_id"), ev.get("ref"))
    if ev["event_type"] == "follow_up.scheduled" and ev.get("ref"):
        conn = connect()
        try:
            row = conn.execute("SELECT title, due_date, assignee, asset_id FROM follow_ups WHERE follow_up_id=?", (ev["ref"],)).fetchone()
        finally:
            conn.close()
        if row and row["due_date"]:
            out.update(reports.calendar_links(row["title"], row["due_date"],
                                              f"{row['assignee'] or ''} · {row['asset_id'] or ''} · Shifttrace {ev['ref']}\n{out.get('audit', '')}"))
    return out


def _link_lines(ev: dict[str, Any]) -> list[tuple[str, str]]:
    ls = links(ev)
    picked = [(label, ls[k]) for k, label in LINK_LABELS if ls.get(k)]
    if any(k in ls for k in ("handoff", "audit")):
        picked = [p for p in picked if p[0] != "Machine"]
    return picked


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def attachments(ev: dict[str, Any]) -> list[tuple[str, bytes, str]]:
    """Files attached where a channel accepts them: the handoff report when a handoff is published."""
    if ev["event_type"] != "handoff.published" or not (ev.get("ref") or "").startswith("H-"):
        return []
    from . import reports
    out = []
    h = reports.handoff_html(ev["ref"])
    if h:
        out.append((f"handoff-{ev['ref']}.html", h.encode("utf-8"), "text/html"))
    x = reports.handoff_xlsx(ev["ref"])
    if x:
        out.append((f"handoff-{ev['ref']}.xlsx", x, XLSX))
    return out


def _plain(ev: dict[str, Any]) -> str:
    title = EVENT_TITLES.get(ev["event_type"], ev["event_type"])
    lines = [f"{title} · {ev['asset_id']}", ev["summary"]]
    lines += [f"{label}: {url}" for label, url in _link_lines(ev)]
    lines.append(f"{ev['ref'] or ''} · Shifttrace (synthetic demo data)")
    return "\n".join(lines)


def _request(cid: str, ev: dict[str, Any]) -> tuple[str, dict[str, str], bytes] | None:
    title = EVENT_TITLES.get(ev["event_type"], ev["event_type"])
    line = f"{title} · {ev['asset_id']}: {ev['summary']}"
    if cid in ("webhook", "local"):
        url = _env("WEBHOOK_URL") if cid == "webhook" else f"http://127.0.0.1:{settings.api_port}/api/integrations/receiver"
        secret = _env("WEBHOOK_SECRET") if cid == "webhook" else local_secret()
        body = json.dumps(_envelope(ev), default=str).encode()
        headers = {"content-type": "application/json", "X-Shifttrace-Event": ev["event_type"]}
        if secret:
            headers["X-Shifttrace-Signature"] = _sign(body, secret)
        return url, headers, body
    if cid == "slack":
        emoji = {"escalation.raised": ":rotating_light:", "reading.out_of_limit": ":warning:", "order.submitted": ":package:",
                 "transfer.posted": ":arrows_counterclockwise:", "follow_up.scheduled": ":calendar:", "handoff.published": ":clipboard:",
                 "training.recorded": ":mortar_board:", "work_order.updated": ":wrench:"}.get(ev["event_type"], ":bell:")
        link_txt = "".join(f"\n<{url}|{label}>" for label, url in _link_lines(ev))
        msg = {"text": f"{emoji} *{title}* · {ev['asset_id']}\n{ev['summary']}{link_txt}\n_{ev['ref'] or ''} · Shifttrace (synthetic demo data)_"}
        return _env("SLACK_WEBHOOK_URL"), {"content-type": "application/json"}, json.dumps(msg).encode()
    if cid == "teams":
        msg = {"@type": "MessageCard", "@context": "https://schema.org/extensions", "summary": line, "themeColor": "2DD4BF",
               "title": f"{title} · {ev['asset_id']}", "text": f"{ev['summary']}  \n" + "".join(f"[{label}]({url})  \n" for label, url in _link_lines(ev)) + f"{ev['ref'] or ''} (Shifttrace, synthetic demo data)"}
        return _env("TEAMS_WEBHOOK_URL"), {"content-type": "application/json"}, json.dumps(msg).encode()
    if cid == "excel":
        ls = links(ev)
        row = {"time": ev["ts"], "event": title, "event_type": ev["event_type"], "machine": ev["asset_id"], "ref": ev["ref"], "summary": ev["summary"],
               "session": ev["session_id"], "handoff_report": ls.get("handoff", ""), "handoff_excel": ls.get("handoff_excel", ""), "audit_log": ls.get("audit", ""),
               "calendar": ls.get("google_calendar", ""), "synthetic_demo_data": True}
        return _env("SPREADSHEET_WEBHOOK_URL"), {"content-type": "application/json"}, json.dumps(row, default=str).encode()
    if cid == "jira":
        auth = base64.b64encode(f"{_env('JIRA_EMAIL')}:{_env('JIRA_API_TOKEN')}".encode()).decode()
        body = {"fields": {"project": {"key": _env("JIRA_PROJECT_KEY")}, "issuetype": {"name": "Task"},
                           "summary": f"[Shifttrace] {title}: {ev['summary']}"[:250],
                           "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [
                               {"type": "text", "text": json.dumps(_envelope(ev), default=str, indent=1)[:3000]}]}]}}}
        return f"{_env('JIRA_BASE_URL').rstrip('/')}/rest/api/3/issue", {"content-type": "application/json", "authorization": f"Basic {auth}"}, json.dumps(body).encode()
    if cid == "github":
        body = {"title": f"[Shifttrace] {title}: {ev['summary']}"[:250],
                "body": f"{ev['summary']}\n\n" + "".join(f"- [{label}]({url})\n" for label, url in _link_lines(ev)) + f"\n```json\n{json.dumps(_envelope(ev), default=str, indent=1)}\n```\n_Synthetic demo data from Shifttrace._",
                "labels": ["shifttrace", ev["event_type"].split(".")[0]]}
        return (f"https://api.github.com/repos/{_env('GITHUB_REPO')}/issues",
                {"accept": "application/vnd.github+json", "authorization": f"Bearer {_env('GITHUB_TOKEN')}", "content-type": "application/json"}, json.dumps(body).encode())
    return None


def local_secret() -> str:
    """Per-process secret for the local test receiver (so signature checking is exercised end to end)."""
    global _LOCAL_SECRET
    if not _LOCAL_SECRET:
        _LOCAL_SECRET = hashlib.sha256(f"{settings.mcp_token}:local-receiver".encode()).hexdigest()
    return _LOCAL_SECRET


_LOCAL_SECRET = ""


def _load_event(eid: int) -> dict[str, Any]:
    conn = connect()
    try:
        return rows_to_dicts(conn.execute("SELECT * FROM integration_events WHERE id=?", (eid,)).fetchall())[0]
    finally:
        conn.close()


async def deliver(eid: int, only: str | None = None) -> list[dict[str, Any]]:
    ev = _load_event(eid)
    out = []
    for c in connectors():
        if not c["enabled"] or (only and c["id"] != only) or (c["events"] != "all" and ev["event_type"] not in c["events"]):
            continue
        out.append(await _deliver_one(c, ev))
    return out


CHAT = {"telegram": "api.telegram.org", "whatsapp": "graph.facebook.com"}


async def _deliver_one(c: dict[str, Any], ev: dict[str, Any]) -> dict[str, Any]:
    if c["id"] in CHAT:
        url, headers, body = "", {}, b""
        target = CHAT[c["id"]]  # the Telegram token is part of its URL: never store or show the URL
    else:
        req = _request(c["id"], ev)
        if req is None:
            return {}
        url, headers, body = req
        target = url.split("?")[0]
        target = target if c["id"] in ("local",) else target[:60] + ("…" if len(target) > 60 else "")  # never show tokens in query strings
    status, code, detail, attempts = "failed", None, "", 0
    for attempts in range(1, 4):
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=c["id"] == "excel") as client:
                if c["id"] in CHAT:
                    code, status, detail = await _send_chat(c["id"], ev, client)
                else:
                    r = await client.post(url, headers=headers, content=body)
                    code = r.status_code
                    status, detail = ("delivered", _detail(c["id"], r)) if _ok(r) else ("failed", f"HTTP {r.status_code}: {r.text[:160]}")
            if status in ("delivered", "partial"):
                break  # partial: the message went out but a file did not; retrying would send the message twice
            if code and code < 500 and code != 429:
                break  # a client error will not fix itself on retry
        except httpx.HTTPError as e:
            detail = f"{type(e).__name__}: {e}"[:200]
        await asyncio.sleep(1.5 * attempts)
    with tx() as conn:
        conn.execute("""INSERT INTO integration_deliveries(event_id, connector, target, status, http_status, detail, attempts, ts)
                        VALUES (?,?,?,?,?,?,?,?)""", (ev["id"], c["id"], target, status, code, detail, attempts, utcnow()))
    if status != "delivered":
        log.warning("integration %s failed for event %s: %s", c["id"], ev["id"], detail)
    from .bus import bus
    bus.publish("integration", {"event_id": ev["id"], "connector": c["id"], "status": status})
    return {"connector": c["id"], "status": status, "http_status": code, "detail": detail}


def _ok(r: httpx.Response) -> bool:
    return 200 <= r.status_code < 300


async def _send_chat(cid: str, ev: dict[str, Any], client: httpx.AsyncClient) -> tuple[int, str, str]:
    """Send the message, then attach the report files. Returns (http status, delivered|partial|failed, detail)."""
    text = _plain(ev)
    files = attachments(ev)
    if cid == "telegram":
        base = f"https://api.telegram.org/bot{_env('TELEGRAM_BOT_TOKEN')}"
        chat = _env("TELEGRAM_CHAT_ID")
        r = await client.post(f"{base}/sendMessage", json={"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True})
        if not _ok(r):
            return r.status_code, "failed", f"HTTP {r.status_code}: {r.text[:160]}"
        sent = [f"message {(r.json().get('result') or {}).get('message_id')}"]
        for name, data, mime in files:
            d = await client.post(f"{base}/sendDocument", data={"chat_id": chat, "caption": f"{ev['ref']} · {name.rsplit('.', 1)[-1].upper()} report"},
                                  files={"document": (name, data, mime)})
            if not _ok(d):
                return d.status_code, "partial", f"{', '.join(sent)}; attaching {name} failed: HTTP {d.status_code}: {d.text[:120]}"
            sent.append(name)
        return r.status_code, "delivered", "sent " + ", ".join(sent)
    # WhatsApp Cloud API
    base = f"https://graph.facebook.com/{_env('WHATSAPP_API_VERSION') or 'v21.0'}/{_env('WHATSAPP_PHONE_NUMBER_ID')}"
    auth = {"authorization": f"Bearer {_env('WHATSAPP_TOKEN')}"}
    to = _env("WHATSAPP_TO")
    if _env("WHATSAPP_TEMPLATE"):
        msg = {"messaging_product": "whatsapp", "to": to, "type": "template",
               "template": {"name": _env("WHATSAPP_TEMPLATE"), "language": {"code": _env("WHATSAPP_TEMPLATE_LANG") or "en"},
                            "components": [{"type": "body", "parameters": [{"type": "text", "text": text.replace("\n", " · ")[:1000]}]}]}}
    else:
        msg = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text[:4000], "preview_url": False}}
    r = await client.post(f"{base}/messages", json=msg, headers=auth)
    if not _ok(r):
        return r.status_code, "failed", f"HTTP {r.status_code}: {r.text[:160]}"
    sent = ["message " + str(((r.json().get("messages") or [{}])[0]).get("id", ""))[:24]]
    for name, data, mime in files:
        if mime != XLSX:  # WhatsApp documents accept PDF, Office and plain text, not HTML
            continue
        up = await client.post(f"{base}/media", headers=auth, data={"messaging_product": "whatsapp", "type": mime}, files={"file": (name, data, mime)})
        if not _ok(up):
            return up.status_code, "partial", f"{sent[0]}; uploading {name} failed: HTTP {up.status_code}: {up.text[:120]}"
        doc = {"messaging_product": "whatsapp", "to": to, "type": "document",
               "document": {"id": up.json().get("id"), "filename": name, "caption": f"Shift handoff {ev['ref']}"}}
        d = await client.post(f"{base}/messages", json=doc, headers=auth)
        if not _ok(d):
            return d.status_code, "partial", f"{sent[0]}; sending {name} failed: HTTP {d.status_code}: {d.text[:120]}"
        sent.append(name)
    return r.status_code, "delivered", "sent " + ", ".join(sent)


def _detail(cid: str, r: httpx.Response) -> str:
    try:
        j = r.json()
    except ValueError:
        return f"HTTP {r.status_code}"
    if cid == "jira":
        return f"created {j.get('key')}"
    if cid == "github":
        return f"created issue #{j.get('number')} {j.get('html_url', '')}"
    if cid == "local":
        return f"signature {'valid' if j.get('signature_valid') else 'INVALID'}"
    return f"HTTP {r.status_code}"


def verify_local(body: bytes, signature: str | None) -> bool:
    return bool(signature) and hmac.compare_digest(_sign(body, local_secret()), signature or "")


# --------------------------------------------------------------------------- calendar (.ics) for follow-ups

def ics(follow_ups: list[dict[str, Any]]) -> str:
    def esc(t: str) -> str:
        return (t or "").replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Shifttrace//Follow-ups//EN", "CALSCALE:GREGORIAN", "X-WR-CALNAME:Shifttrace follow-ups"]
    stamp = utcnow().replace("-", "").replace(":", "")
    for f in follow_ups:
        if not f.get("due_date"):
            continue
        d = f["due_date"].replace("-", "")
        desc = f"{f.get('assignee') or ''} - {f.get('asset_id') or ''} - Shifttrace {f['follow_up_id']}"
        lines += ["BEGIN:VEVENT", f"UID:{f['follow_up_id']}@shifttrace", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{d}",
                  f"SUMMARY:{esc(f['title'])}", f"DESCRIPTION:{esc(desc)}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
