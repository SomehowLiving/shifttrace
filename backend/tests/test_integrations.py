"""Connected systems: verified actions become events, delivered (signed) to configured connectors and logged."""
import asyncio
import hashlib
import hmac
import json

import httpx

from app import integrations, tools
from app.db import connect, tx, utcnow


def _session(asset="DC2-ZB", task="warehouse_ops"):
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status, task_id) VALUES (?,?,?,?,?,?,?)",
                     ("S-1001", asset, "Kavya Rao", "A shift", utcnow(), "ACTIVE", task))
    return "S-1001"


def _fake_http(monkeypatch, seen):
    real = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if "github" in str(request.url):
            return httpx.Response(201, json={"number": 7, "html_url": "https://github.com/acme/plant/issues/7"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(integrations.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))


def test_nothing_is_sent_when_no_connector_is_configured(monkeypatch):
    for k in ("WEBHOOK_URL", "SLACK_WEBHOOK_URL", "TEAMS_WEBHOOK_URL", "JIRA_BASE_URL", "GITHUB_TOKEN", "TELEGRAM_BOT_TOKEN", "WHATSAPP_TOKEN", "SPREADSHEET_WEBHOOK_URL"):
        monkeypatch.delenv(k, raising=False)
    assert [c["id"] for c in integrations.connectors() if c["enabled"]] == []
    seen = []
    _fake_http(monkeypatch, seen)
    sid = _session()
    asyncio.run(tools.run_tool("schedule_follow_up", {}, sid, "test", lambda c: tools.schedule_follow_up(c, "Recount B-06-1", "tomorrow", None)))
    conn = connect()
    try:
        ev = conn.execute("SELECT event_type, ref FROM integration_events").fetchall()
    finally:
        conn.close()
    assert [tuple(e) for e in ev] == [("follow_up.scheduled", "FU-5001")] and seen == []  # recorded, not sent anywhere


def test_verified_action_is_delivered_signed_to_webhook_slack_and_github(monkeypatch):
    monkeypatch.setenv("WEBHOOK_URL", "https://hooks.example.test/shifttrace")
    monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.example.test/T/B/X")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    monkeypatch.setenv("GITHUB_REPO", "acme/plant")
    seen = []
    _fake_http(monkeypatch, seen)
    sid = _session(asset="C-204", task="troubleshoot")
    out = asyncio.run(tools.run_tool("escalate_incident", {}, sid, "test",
                                     lambda c: tools.escalate_incident(c, None, "high", "Vibration rising past alarm level")))
    assert "queued for delivery to" in out["message"] and "Slack" in out["message"]

    async def settle():
        conn = connect()
        try:
            eid = conn.execute("SELECT id FROM integration_events WHERE event_type='escalation.raised'").fetchone()[0]
        finally:
            conn.close()
        return await integrations.deliver(eid)
    results = asyncio.run(settle())
    assert {r["connector"]: r["status"] for r in results} == {"webhook": "delivered", "slack": "delivered", "github": "delivered"}
    hook = next(r for r in seen if "hooks.example.test" in str(r.url))
    expected = "sha256=" + hmac.new(b"s3cret", hook.content, hashlib.sha256).hexdigest()
    assert hook.headers["X-Shifttrace-Signature"] == expected
    body = json.loads(hook.content)
    assert body["event_type"] == "escalation.raised" and body["data"]["severity"] == "high" and body["synthetic_demo_data"] is True
    assert "ghp_test" not in hook.content.decode() and "s3cret" not in hook.content.decode()  # no credentials in payloads
    gh = next(r for r in seen if "api.github.com" in str(r.url))
    assert json.loads(gh.content)["title"].startswith("[Shifttrace] Escalation raised")
    conn = connect()
    try:
        d = conn.execute("SELECT connector, status, detail FROM integration_deliveries WHERE connector='github' ORDER BY id DESC").fetchone()
    finally:
        conn.close()
    assert d["status"] == "delivered" and "issue #7" in d["detail"]


def test_local_receiver_checks_the_signature():
    body = b'{"event_type":"integration.test"}'
    good = "sha256=" + hmac.new(integrations.local_secret().encode(), body, hashlib.sha256).hexdigest()
    assert integrations.verify_local(body, good) and not integrations.verify_local(body, "sha256=bad") and not integrations.verify_local(body, None)


def test_unverified_or_read_only_calls_emit_nothing():
    assert integrations.event_for("check_inventory", {}, {"ok": True}, "S-1", "C-204") is None
    assert integrations.event_for("schedule_follow_up", {}, {"duplicate": True, "verified": True}, "S-1", "C-204") is None
    assert integrations.event_for("record_reading", {}, {"evaluation": "normal", "verified": True}, "S-1", "C-204") is None
    e = integrations.event_for("record_reading", {"reading": "cold room", "value": 9.1, "unit": "C"}, {"evaluation": "out_of_limit", "event_id": 3}, "S-1", "DC2-ZB")
    assert e["event_type"] == "reading.out_of_limit"


def _chat_http(monkeypatch, seen, fail_document=False):
    real = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        u = str(request.url)
        if "api.telegram.org" in u:
            if fail_document and u.endswith("/sendDocument"):
                return httpx.Response(400, json={"ok": False, "description": "Bad Request: file too big"})
            return httpx.Response(200, json={"ok": True, "result": {"message_id": 41}})
        if u.endswith("/media"):
            return httpx.Response(200, json={"id": "MEDIA-1"})
        if "graph.facebook.com" in u:
            return httpx.Response(200, json={"messages": [{"id": "wamid.TEST"}]})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(integrations.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))


def _handoff_event(sid):
    out = asyncio.run(tools.run_tool("create_shift_handoff", {}, sid, "test", lambda c: tools.create_shift_handoff(c)))
    conn = connect()
    try:
        eid = conn.execute("SELECT id FROM integration_events WHERE event_type='handoff.published'").fetchone()[0]
    finally:
        conn.close()
    return out, eid


def test_handoff_goes_to_telegram_whatsapp_and_excel_with_links_and_report_attached(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:SECRETTOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100200")
    monkeypatch.setenv("WHATSAPP_TOKEN", "EAAG-secret")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "555")
    monkeypatch.setenv("WHATSAPP_TO", "919800000000")
    monkeypatch.setenv("SPREADSHEET_WEBHOOK_URL", "https://prod.example.test/workflows/abc/invoke")
    monkeypatch.setenv("PUBLIC_CONSOLE_URL", "https://shifttrace.plant.example.test/")
    sid = _session(asset="C-204", task="troubleshoot")
    out, eid = _handoff_event(sid)  # before faking HTTP: the fake replaces httpx.AsyncClient for every module
    seen = []
    _chat_http(monkeypatch, seen)
    hid = out["handoff_id"]
    results = {r["connector"]: r for r in asyncio.run(integrations.deliver(eid))}
    assert {k: v["status"] for k, v in results.items()} == {"telegram": "delivered", "whatsapp": "delivered", "excel": "delivered"}

    tg = [r for r in seen if "api.telegram.org" in str(r.url)]
    assert [str(r.url).rsplit("/", 1)[-1] for r in tg] == ["sendMessage", "sendDocument", "sendDocument"]
    text = json.loads(tg[0].content)["text"]
    assert f"Handoff report: https://shifttrace.plant.example.test/handoffs/{hid}" in text and "Audit log: " in text
    assert f'filename="handoff-{hid}.html"'.encode() in tg[1].content and f'filename="handoff-{hid}.xlsx"'.encode() in tg[2].content

    wa = [r for r in seen if "graph.facebook.com" in str(r.url)]
    assert [str(r.url).rsplit("/", 1)[-1] for r in wa] == ["messages", "media", "messages"]  # text, upload the Excel, document message
    assert json.loads(wa[2].content)["document"] == {"id": "MEDIA-1", "filename": f"handoff-{hid}.xlsx", "caption": f"Shift handoff {hid}"}
    assert wa[0].headers["authorization"] == "Bearer EAAG-secret"

    row = json.loads(next(r for r in seen if "prod.example.test" in str(r.url)).content)
    assert row["handoff_report"].endswith(f"/handoffs/{hid}") and row["handoff_excel"].endswith(f"/api/handoffs/{hid}/report.xlsx")

    conn = connect()
    try:
        targets = [r[0] for r in conn.execute("SELECT target FROM integration_deliveries")]
    finally:
        conn.close()
    assert "SECRETTOKEN" not in " ".join(targets) and "api.telegram.org" in targets  # the bot token (part of the URL) is never logged


def test_a_failed_attachment_is_reported_partial_and_the_message_is_not_resent(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:T")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    _, eid = _handoff_event(_session(asset="C-204", task="troubleshoot"))
    seen = []
    _chat_http(monkeypatch, seen, fail_document=True)
    r = asyncio.run(integrations.deliver(eid, only="telegram"))[0]
    assert r["status"] == "partial" and "attaching" in r["detail"]
    assert sum(1 for x in seen if str(x.url).endswith("/sendMessage")) == 1


def test_follow_up_messages_carry_add_to_calendar_links():
    sid = _session()
    asyncio.run(tools.run_tool("schedule_follow_up", {}, sid, "test", lambda c: tools.schedule_follow_up(c, "Recount B-06-1", "tomorrow", "B shift")))
    conn = connect()
    try:
        ev = dict(conn.execute("SELECT * FROM integration_events WHERE event_type='follow_up.scheduled'").fetchone())
        due = conn.execute("SELECT due_date FROM follow_ups WHERE follow_up_id=?", (ev["ref"],)).fetchone()[0]
    finally:
        conn.close()
    ls = integrations.links(ev)
    assert due and "calendar.google.com/calendar/render?action=TEMPLATE" in ls["google_calendar"] and due.replace("-", "") in ls["google_calendar"]
    assert "outlook.live.com" in ls["outlook_calendar"] and "Recount" in integrations._plain(ev)


def test_follow_ups_export_as_calendar():
    text = integrations.ics([{"follow_up_id": "FU-5001", "title": "Recount, B-06-1", "due_date": "2026-11-22", "assignee": "A shift", "asset_id": "DC2-ZB"}])
    assert "BEGIN:VEVENT" in text and "DTSTART;VALUE=DATE:20261122" in text and "SUMMARY:Recount\\, B-06-1" in text
