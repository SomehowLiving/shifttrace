"""Domain logic beyond maintenance: warehouse and logistics, follow-ups, training and onboarding.

Same rules as the maintenance tools: data comes from packs, consequential changes need the worker's spoken yes after
a read-back (or a console click), every write is re-read before it is reported, and judgements that can be made in
code (stock sufficiency, quiz scoring) are made in code, not by the language model.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from .db import next_id, row_to_dict, rows_to_dicts, utcnow
from .services import ServiceError, SessionContext, _single_part, get_asset, normalize_id

# --------------------------------------------------------------------------- shipments

def _shipment_view(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    sh = dict(row)
    sh["items"] = json.loads(sh.pop("items_json") or "[]")
    sh["events"] = rows_to_dicts(conn.execute(
        "SELECT ts, location, status, note FROM shipment_events WHERE shipment_id=? ORDER BY ts DESC", (sh["shipment_id"],)).fetchall())
    return sh


def find_shipments(conn: sqlite3.Connection, ctx: SessionContext, reference: str | None) -> list[dict[str, Any]]:
    """By shipment ID ('4471', 'SHP 4471'), carrier reference, or an item / part name on board."""
    rows = conn.execute("SELECT * FROM shipments ORDER BY updated_at DESC").fetchall()
    if not reference:
        return [_shipment_view(conn, r) for r in rows if r["asset_id"] in (None, ctx.asset_id)][:5]
    ref = reference.strip()
    sid = normalize_id(ref, "SHP")
    exact = [r for r in rows if r["shipment_id"].upper() == sid.upper() or (r["carrier_ref"] or "").upper() == ref.upper()]
    if exact:
        return [_shipment_view(conn, r) for r in exact]
    words = {w for w in re.findall(r"[a-z0-9]+", ref.lower()) if len(w) > 2} - {"shipment", "delivery", "the", "where", "truck", "order"}
    hits = []
    for r in rows:
        hay = f"{r['shipment_id']} {r['carrier']} {r['origin']} {r['destination']} {r['items_json']}".lower()
        if words and any(w in hay for w in words):
            hits.append(_shipment_view(conn, r))
    if not hits:
        raise ServiceError("shipment_not_found", f"No shipment matches '{reference}'.",
                           known=[{"shipment_id": r["shipment_id"], "status": r["status"]} for r in rows[:6]])
    return hits


# --------------------------------------------------------------------------- stock transfers

def _transfer(conn: sqlite3.Connection, transfer_id: str) -> dict[str, Any]:
    tid = normalize_id(transfer_id, "TR")
    row = conn.execute("""SELECT t.*, p.name AS part_name FROM stock_transfers t JOIN parts p ON p.part_id=t.part_id
                          WHERE upper(t.transfer_id)=upper(?)""", (tid,)).fetchone()
    if row is None:
        raise ServiceError("transfer_not_found", f"No stock transfer {tid}.")
    return row_to_dict(row)  # type: ignore[return-value]


def get_transfer(conn: sqlite3.Connection, transfer_id: str) -> dict[str, Any]:
    return _transfer(conn, transfer_id)


def _location(conn: sqlite3.Connection, part_id: str, raw: str) -> str:
    """'reserve R twelve', 'r-12', 'DC2-R-12' -> the stocked location id for this part (or a known bin)."""
    known = [r["location"] for r in conn.execute("SELECT DISTINCT location FROM stock_levels").fetchall()]
    q = re.sub(r"[^a-z0-9]", "", raw.lower().replace("twelve", "12").replace("zero", "0").replace("four", "4").replace("two", "2"))
    best = [k for k in known if re.sub(r"[^a-z0-9]", "", k.lower()).endswith(q) or q.endswith(re.sub(r"[^a-z0-9]", "", k.lower()))]
    if len(best) == 1:
        return best[0]
    exact = [k for k in known if k.lower() == raw.strip().lower()]
    if exact:
        return exact[0]
    raise ServiceError("location_unknown", f"'{raw}' is not a known location.", known_locations=known)


def create_transfer(conn: sqlite3.Connection, ctx: SessionContext, part: str, quantity: int, from_location: str,
                    to_location: str, reason: str | None) -> dict[str, Any]:
    if quantity < 1 or quantity > 500:
        raise ServiceError("bad_quantity", "Quantity must be between 1 and 500.")
    p = _single_part(conn, part, None)
    src, dst = _location(conn, p["part_id"], from_location), _location(conn, p["part_id"], to_location)
    if src == dst:
        raise ServiceError("same_location", "From and to are the same location.")
    have = conn.execute("SELECT quantity FROM stock_levels WHERE part_id=? AND location=?", (p["part_id"], src)).fetchone()
    if not have or have["quantity"] < quantity:
        raise ServiceError("insufficient_stock", f"Only {have['quantity'] if have else 0} of {p['part_id']} at {src}; cannot move {quantity}.",
                           available=have["quantity"] if have else 0)
    existing = conn.execute("""SELECT transfer_id FROM stock_transfers WHERE part_id=? AND from_location=? AND to_location=? AND quantity=?
                               AND status='PENDING_CONFIRMATION'""", (p["part_id"], src, dst, quantity)).fetchone()
    if existing:
        return {"transfer": _transfer(conn, existing["transfer_id"]), "duplicate": True}
    tid = next_id(conn, "transfer", "TR-", 6001)
    watermark = conn.execute("SELECT IFNULL(max(id), 0) FROM transcript_events").fetchone()[0]
    conn.execute("""INSERT INTO stock_transfers(transfer_id, part_id, quantity, from_location, to_location, reason, status, session_id,
                    asset_id, created_by, transcript_watermark, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                 (tid, p["part_id"], quantity, src, dst, reason, "PENDING_CONFIRMATION", ctx.session_id, ctx.asset_id, ctx.technician,
                  watermark, utcnow()))
    return {"transfer": _transfer(conn, tid), "duplicate": False}


def confirm_transfer(conn: sqlite3.Connection, transfer_id: str, by: str, via: str, evidence: str) -> dict[str, Any]:
    t = _transfer(conn, transfer_id)
    if t["status"] == "DONE":
        return {"transfer": t, "duplicate": True}
    if t["status"] != "PENDING_CONFIRMATION":
        raise ServiceError("invalid_state", f"{t['transfer_id']} is {t['status']}.")
    have = conn.execute("SELECT quantity FROM stock_levels WHERE part_id=? AND location=?", (t["part_id"], t["from_location"])).fetchone()
    now = utcnow()
    if not have or have["quantity"] < t["quantity"]:
        reason = f"Stock at {t['from_location']} changed: only {have['quantity'] if have else 0} left."
        conn.execute("UPDATE stock_transfers SET status='FAILED', failure_reason=?, decided_at=? WHERE transfer_id=?", (reason, now, t["transfer_id"]))
        return {"transfer": _transfer(conn, t["transfer_id"]), "duplicate": False}
    conn.execute("UPDATE stock_levels SET quantity=quantity-? WHERE part_id=? AND location=?", (t["quantity"], t["part_id"], t["from_location"]))
    conn.execute("""INSERT INTO stock_levels(part_id, location, quantity) VALUES (?,?,?)
                    ON CONFLICT(part_id, location) DO UPDATE SET quantity=quantity+excluded.quantity""", (t["part_id"], t["to_location"], t["quantity"]))
    erp_ref = next_id(conn, "erp", "ERP-", 70001)
    conn.execute("INSERT INTO erp_postings VALUES (?,?,?,?,?,?)",
                 (erp_ref, now, "STOCK_TRANSFER", t["transfer_id"], json.dumps({k: t[k] for k in ("part_id", "quantity", "from_location", "to_location")}), "POSTED"))
    conn.execute("""UPDATE stock_transfers SET status='DONE', confirmed_by=?, confirmation_via=?, confirmation_evidence=?, erp_ref=?, decided_at=?
                    WHERE transfer_id=?""", (by, via, evidence, erp_ref, now, t["transfer_id"]))
    return {"transfer": _transfer(conn, t["transfer_id"]), "duplicate": False}


def cancel_transfer(conn: sqlite3.Connection, transfer_id: str, by: str, via: str) -> dict[str, Any]:
    t = _transfer(conn, transfer_id)
    if t["status"] != "PENDING_CONFIRMATION":
        raise ServiceError("invalid_state", f"{t['transfer_id']} is {t['status']}; it cannot be cancelled.")
    conn.execute("UPDATE stock_transfers SET status='CANCELLED', confirmed_by=?, confirmation_via=?, decided_at=? WHERE transfer_id=?",
                 (by, via, utcnow(), t["transfer_id"]))
    return _transfer(conn, t["transfer_id"])


# --------------------------------------------------------------------------- follow-ups

_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def parse_due(text: str | None, now: datetime | None = None) -> str | None:
    """Spoken due dates -> ISO date where it is unambiguous ('today', 'tomorrow', 'next shift', 'in 3 days', a weekday, 2026-11-24)."""
    if not text:
        return None
    now = now or datetime.now(timezone.utc)
    t = text.strip().lower()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        return t
    if "today" in t or "this shift" in t:
        d = now
    elif "tomorrow" in t or "next shift" in t:
        d = now + timedelta(days=1)
    elif m := re.search(r"in (\d+) days?", t):
        d = now + timedelta(days=int(m.group(1)))
    elif "next week" in t:
        d = now + timedelta(days=7)
    elif any(w in t for w in _WEEKDAYS):
        wd = next(i for i, w in enumerate(_WEEKDAYS) if w in t)
        d = now + timedelta(days=(wd - now.weekday()) % 7 or 7)
    else:
        return None
    return d.date().isoformat()


def create_follow_up(conn: sqlite3.Connection, ctx: SessionContext, title: str, due: str | None, assignee: str | None) -> dict[str, Any]:
    title = (title or "").strip()
    if len(title) < 4:
        raise ServiceError("bad_title", "Say what the follow-up is.")
    existing = conn.execute("SELECT follow_up_id FROM follow_ups WHERE session_id IS ? AND lower(title)=lower(?) AND status='OPEN'",
                            (ctx.session_id, title)).fetchone()
    if existing:
        return {"follow_up": row_to_dict(conn.execute("SELECT * FROM follow_ups WHERE follow_up_id=?", (existing["follow_up_id"],)).fetchone()), "duplicate": True}
    fid = next_id(conn, "follow_up", "FU-", 5001)
    conn.execute("INSERT INTO follow_ups VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (fid, title, due, parse_due(due), assignee or "next shift", ctx.asset_id, ctx.session_id, ctx.technician, "OPEN", utcnow()))
    return {"follow_up": row_to_dict(conn.execute("SELECT * FROM follow_ups WHERE follow_up_id=?", (fid,)).fetchone()), "duplicate": False}


# --------------------------------------------------------------------------- training and onboarding

def modules(asset: dict[str, Any]) -> list[dict[str, Any]]:
    return list((asset.get("metadata") or {}).get("training") or [])


def get_module(asset: dict[str, Any], module_id: str | None) -> dict[str, Any]:
    mods = modules(asset)
    if not mods:
        raise ServiceError("no_training", f"No training module is configured for {asset['asset_id']}.")
    if not module_id:
        return mods[0]
    for m in mods:
        if m["module_id"].lower() == module_id.lower() or module_id.lower() in m["title"].lower():
            return m
    raise ServiceError("module_not_found", f"No module '{module_id}'.", modules=[{"module_id": m["module_id"], "title": m["title"]} for m in mods])


def _norm(text: str) -> str:
    t = text.lower()
    for w, d in (("zero", "0"), ("one", "1"), ("two", "2"), ("three", "3"), ("four", "4"), ("five", "5"), ("six", "6"), ("seven", "7"),
                 ("eight", "8"), ("nine", "9"), (" point ", "."), ("-", " ")):
        t = t.replace(w, d)
    return re.sub(r"\s+", " ", t)


def evaluate_answer(question: dict[str, Any], answer: str) -> dict[str, Any]:
    """Deterministic marking against the key points configured in the pack. Each key point is a list of acceptable
    phrasings; the answer earns the point if any phrasing appears. correct = enough points, partly = some, incorrect = none."""
    a = _norm(answer)
    points = question.get("key_points") or []
    hit, missed = [], []
    for alts in points:
        (hit if any(_norm(x) in a for x in alts) else missed).append(alts[0])
    need = question.get("min_points") or len(points)
    result = "correct" if len(hit) >= need else "partly" if hit else "incorrect"
    return {"result": result, "matched": hit, "missing": missed, "needed": need}


def record_answer(conn: sqlite3.Connection, ctx: SessionContext, module: dict[str, Any], question_id: str, answer: str) -> dict[str, Any]:
    q = next((x for x in module["questions"] if x["id"].lower() == question_id.lower()), None)
    if q is None:
        raise ServiceError("question_not_found", f"No question '{question_id}' in {module['module_id']}.",
                           questions=[x["id"] for x in module["questions"]])
    ev = evaluate_answer(q, answer)
    conn.execute("""INSERT INTO training_answers(session_id, trainee, module_id, question_id, answer, result, matched_json, ts)
                    VALUES (?,?,?,?,?,?,?,?)""", (ctx.session_id, ctx.technician, module["module_id"], q["id"], answer, ev["result"],
                                                  json.dumps(ev), utcnow()))
    rid = conn.execute("SELECT max(id) FROM training_answers").fetchone()[0]
    return {"answer_id": rid, "question": q, **ev}


def finish_module(conn: sqlite3.Connection, ctx: SessionContext, module: dict[str, Any]) -> dict[str, Any]:
    """Score = latest answer per question (correct 1, partly 0.5) over all questions in the module, so unanswered
    questions count as zero. Pass mark comes from the pack (default 80)."""
    rows = rows_to_dicts(conn.execute("""SELECT question_id, result FROM training_answers WHERE session_id IS ? AND module_id=? ORDER BY id""",
                                      (ctx.session_id, module["module_id"])).fetchall())
    latest = {r["question_id"]: r["result"] for r in rows}
    total = len(module["questions"])
    pts = sum(1.0 if latest.get(q["id"]) == "correct" else 0.5 if latest.get(q["id"]) == "partly" else 0.0 for q in module["questions"])
    score = round(100 * pts / total) if total else 0
    passed = score >= int(module.get("pass_score", 80))
    status = "PASSED" if passed else "NEEDS_REVIEW"
    now = utcnow()
    conn.execute("""INSERT INTO learning_records(trainee, module_id, title, asset_id, status, score, attempts, last_session_id, updated_at)
                    VALUES (?,?,?,?,?,?,1,?,?) ON CONFLICT(trainee, module_id) DO UPDATE SET status=excluded.status, score=excluded.score,
                    attempts=attempts+1, last_session_id=excluded.last_session_id, updated_at=excluded.updated_at, title=excluded.title""",
                 (ctx.technician, module["module_id"], module["title"], ctx.asset_id, status, score, ctx.session_id, now))
    weak = [q for q in module["questions"] if latest.get(q["id"]) != "correct"]
    return {"score": score, "status": status, "passed": passed, "answered": len(latest), "total": total,
            "pass_score": int(module.get("pass_score", 80)),
            "review": [{"question_id": q["id"], "ask": q["ask"], "section": q.get("section"), "result": latest.get(q["id"], "not answered")} for q in weak]}


def asset_for(conn: sqlite3.Connection, ctx: SessionContext) -> dict[str, Any]:
    return get_asset(conn, ctx.asset_id)
