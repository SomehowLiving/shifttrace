"""Domain logic for the demo CMMS, inventory, procurement, evidence and handoffs.

Every function takes an open sqlite3 connection. Callers own the transaction.
Mutations return the authoritative row re-read from the database.
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from .db import flag_enabled, next_id, parse_ts, row_to_dict, rows_to_dicts, utcnow

VISION_MODEL_LABEL = "gpt-4o-mini via Agora ConvoAI (camera frames)"


class ServiceError(Exception):
    """Expected business failure: reported honestly to the technician."""

    def __init__(self, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.extra = extra

    def to_dict(self) -> dict[str, Any]:
        return {"ok": False, "error": self.code, "message": self.message, **self.extra}


@dataclass
class SessionContext:
    session_id: str | None
    asset_id: str
    technician: str
    task_id: str | None = None

    @classmethod
    def resolve(cls, conn: sqlite3.Connection, session_id: str | None) -> "SessionContext":
        row = None
        if session_id:
            row = conn.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT * FROM sessions WHERE status='ACTIVE' ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return cls(session_id=None, asset_id=fallback_asset_id(conn), technician="unknown technician")
        return cls(session_id=row["session_id"], asset_id=row["asset_id"], technician=row["technician"],
                   task_id=row["task_id"] if "task_id" in row.keys() else None)


def fallback_asset_id(conn: sqlite3.Connection, session_id: str | None = None) -> str:
    """Asset for records that have no explicit one: the session's asset, else the first loaded asset."""
    if session_id:
        row = conn.execute("SELECT asset_id FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if row:
            return row["asset_id"]
    row = conn.execute("SELECT asset_id FROM assets ORDER BY asset_id LIMIT 1").fetchone()
    return row["asset_id"] if row else "UNKNOWN"


# --------------------------------------------------------------------------- reads

def normalize_id(raw: str, prefix: str) -> str:
    """Spoken/LLM forms -> canonical IDs: '1187', 'wo 1187', 'WO1187', 'work order 1187' -> 'WO-1187'.
    Observed live: the LLM passed '1187' and the lookup failed."""
    s = (raw or "").strip().upper()
    words = {"WO": ("WO", "WORK ORDER", "WORKORDER"), "PR": ("PR", "PROCUREMENT REQUEST", "REQUEST", "P R"),
             "RSV": ("RSV", "RESERVATION"), "ESC": ("ESC", "ESCALATION"), "SHP": ("SHP", "SHIPMENT", "S H P"),
             "TR": ("TR", "TRANSFER", "STOCK TRANSFER", "T R"), "FU": ("FU", "FOLLOW-UP", "FOLLOW UP")}.get(prefix, (prefix,))
    m = re.fullmatch(r"(?:(" + "|".join(re.escape(w) for w in words) + r")[\s#-]*)?(\d{3,6})", s)
    # Only bare numbers or the matching prefix are rewritten; 'C-204' (an asset) must NOT become 'WO-204'.
    return f"{prefix}-{m.group(2)}" if m else s


def normalize_asset(raw: str) -> str:
    s = (raw or "").strip().upper().replace(" ", "")
    m = re.fullmatch(r"([A-Z]+)-?(\d+)", s)
    return f"{m.group(1)}-{m.group(2)}" if m else s


def get_asset(conn: sqlite3.Connection, asset_id: str) -> dict[str, Any]:
    asset_id = normalize_asset(asset_id)
    row = conn.execute("SELECT * FROM assets WHERE upper(asset_id)=upper(?)", (asset_id.strip(),)).fetchone()
    if row is None:
        known = [r["asset_id"] for r in conn.execute("SELECT asset_id FROM assets")]
        raise ServiceError("asset_not_found", f"No asset with ID {asset_id}.", known_assets=known)
    return row_to_dict(row)  # type: ignore[return-value]


def list_assets(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    assets = rows_to_dicts(conn.execute("SELECT * FROM assets ORDER BY asset_id").fetchall())
    for a in assets:
        a["open_work_orders"] = conn.execute(
            "SELECT count(*) FROM work_orders WHERE asset_id=? AND status NOT IN ('CLOSED','RESOLVED')", (a["asset_id"],)
        ).fetchone()[0]
        a["open_loops"] = conn.execute(
            "SELECT count(*) FROM evidence WHERE asset_id=? AND event_type IN ('hypothesis','open_question') AND status='open'",
            (a["asset_id"],),
        ).fetchone()[0]
        h = conn.execute(
            "SELECT handoff_id, created_at, created_by FROM handoffs WHERE asset_id=? ORDER BY created_at DESC LIMIT 1",
            (a["asset_id"],),
        ).fetchone()
        a["latest_handoff"] = dict(h) if h else None
    return assets


def work_order_with_log(conn: sqlite3.Connection, work_order_id: str) -> dict[str, Any]:
    work_order_id = normalize_id(work_order_id, "WO")
    row = conn.execute("SELECT * FROM work_orders WHERE upper(work_order_id)=upper(?)", (work_order_id.strip(),)).fetchone()
    if row is None:
        raise ServiceError("work_order_not_found", f"No work order {work_order_id}.")
    wo = row_to_dict(row)
    wo["log"] = rows_to_dicts(
        conn.execute("SELECT * FROM work_order_log WHERE work_order_id=? ORDER BY ts", (wo["work_order_id"],)).fetchall()
    )
    return wo  # type: ignore[return-value]


def open_work_orders(conn: sqlite3.Connection, asset_id: str) -> list[dict[str, Any]]:
    get_asset(conn, asset_id)
    rows = conn.execute(
        "SELECT work_order_id FROM work_orders WHERE upper(asset_id)=upper(?) AND status NOT IN ('CLOSED','RESOLVED') ORDER BY priority, created_at",
        (asset_id,),
    ).fetchall()
    return [work_order_with_log(conn, r["work_order_id"]) for r in rows]


def asset_history(conn: sqlite3.Connection, asset_id: str, limit_events: int = 40) -> dict[str, Any]:
    asset = get_asset(conn, asset_id)
    aid = asset["asset_id"]
    work_orders = [
        work_order_with_log(conn, r["work_order_id"])
        for r in conn.execute("SELECT work_order_id FROM work_orders WHERE asset_id=? ORDER BY created_at DESC", (aid,))
    ]
    sessions = rows_to_dicts(
        conn.execute(
            "SELECT session_id, technician, shift_label, started_at, ended_at, status, summary FROM sessions WHERE asset_id=? ORDER BY started_at DESC",
            (aid,),
        ).fetchall()
    )
    evidence = rows_to_dicts(
        conn.execute("SELECT * FROM evidence WHERE asset_id=? ORDER BY ts DESC LIMIT ?", (aid, limit_events)).fetchall()
    )
    return {"asset": asset, "work_orders": work_orders, "sessions": sessions, "evidence": evidence}


def latest_handoff(conn: sqlite3.Connection, asset_id: str, exclude_session: str | None = None) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM handoffs WHERE upper(asset_id)=upper(?) AND (? IS NULL OR session_id IS NULL OR session_id != ?) ORDER BY created_at DESC LIMIT 1",
        (asset_id, exclude_session, exclude_session),
    ).fetchone()
    return row_to_dict(row)


def open_items(conn: sqlite3.Connection, asset_id: str) -> list[dict[str, Any]]:
    return rows_to_dicts(
        conn.execute(
            """SELECT e.*, s.technician AS raised_by_technician FROM evidence e LEFT JOIN sessions s ON s.session_id=e.session_id
               WHERE upper(e.asset_id)=upper(?) AND e.event_type IN ('hypothesis','open_question') AND e.status='open'
               ORDER BY e.ts""",
            (asset_id,),
        ).fetchall()
    )


# --------------------------------------------------------------------------- manual retrieval (BM25)

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_STOP = {"the", "a", "an", "of", "to", "and", "or", "is", "are", "for", "in", "on", "with", "what", "how", "do", "does", "i", "it", "this", "that", "be", "at", "by", "should", "can", "my", "we"}


def _tokens(text: str) -> list[str]:
    out = []
    for tok in _TOKEN.findall(text.lower()):
        if tok in _STOP:
            continue
        out.append(tok)
        if "-" in tok:  # "a-17" also matches "17" and "a17"
            out.extend(p for p in tok.split("-") if p and p not in _STOP)
            out.append(tok.replace("-", ""))
    return out


def search_manual(conn: sqlite3.Connection, asset_model: str, query: str, k: int = 3) -> list[dict[str, Any]]:
    chunks = rows_to_dicts(conn.execute("SELECT * FROM manual_chunks WHERE asset_model=?", (asset_model,)).fetchall())
    if not chunks:
        raise ServiceError("no_manual", f"No manual is indexed for model {asset_model}.")
    docs = [_tokens(c["title"]) * 2 + _tokens(c["body"]) for c in chunks]
    avgdl = sum(len(d) for d in docs) / len(docs)
    df: Counter[str] = Counter()
    for d in docs:
        df.update(set(d))
    q = _tokens(query)
    k1, b, n = 1.4, 0.75, len(docs)
    scored = []
    for chunk, d in zip(chunks, docs):
        tf = Counter(d)
        score = 0.0
        for term in q:
            if term not in tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * len(d) / avgdl))
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: -x[0])
    return [
        {"chunk_id": c["chunk_id"], "section": c["section"], "title": c["title"], "text": c["body"], "score": round(s, 2)}
        for s, c in scored[:k]
    ]


# --------------------------------------------------------------------------- inventory

def _part_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return rows_to_dicts(conn.execute("SELECT * FROM parts").fetchall())


def _part_view(conn: sqlite3.Connection, p: dict[str, Any]) -> dict[str, Any]:
    available = p["quantity_on_hand"] - p["quantity_reserved"]
    open_prs = rows_to_dicts(
        conn.execute(
            "SELECT request_id, quantity, status, expected_by FROM procurement_requests WHERE part_id=? AND status IN ('PENDING_APPROVAL','SUBMITTED')",
            (p["part_id"],),
        ).fetchall()
    )
    return {
        "part_id": p["part_id"],
        "name": p["name"],
        "on_hand": p["quantity_on_hand"],
        "reserved": p["quantity_reserved"],
        "available": available,
        "in_stock": available > 0,
        "location": p["location"],
        "lead_time_days": p["lead_time_days"],
        "supplier": p["supplier"],
        "compatible_models": p["compatible_models"],
        "open_procurement_requests": open_prs,
        # warehouse packs keep stock per location (pick face vs reserve); used for stock transfers
        "locations": [{"location": r["location"], "quantity": r["quantity"]} for r in conn.execute(
            "SELECT location, quantity FROM stock_levels WHERE part_id=? ORDER BY location", (p["part_id"],)).fetchall()],
    }


def resolve_parts(conn: sqlite3.Connection, query: str, asset_model: str | None = None) -> list[dict[str, Any]]:
    parts = _part_rows(conn)
    qnorm = query.strip().upper()
    exact = [p for p in parts if p["part_id"].upper() == qnorm]
    if exact:
        return exact
    qtok = set(_tokens(query)) - {"part", "spare", "replacement", "new"}
    scored = []
    for p in parts:
        hay = set(_tokens(f"{p['part_id']} {p['name']} {p['description'] or ''}"))
        overlap = len(qtok & hay)
        if overlap == 0:
            continue
        if "non" in hay and "non" not in qtok:  # "drive end" must not match "non-drive end" equally
            overlap -= 1.5
        bonus = 0.5 if asset_model and asset_model in (p["compatible_models"] or "") else 0.0
        scored.append((overlap + bonus, p))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        return []
    best = scored[0][0]
    return [p for s, p in scored if s >= best - 0.01]


def check_inventory(conn: sqlite3.Connection, query: str, asset_model: str | None = None) -> list[dict[str, Any]]:
    if flag_enabled(conn, "inventory_outage"):
        raise ServiceError("inventory_unavailable", "The inventory service is not responding (simulated outage). Stock levels are unknown; nothing was reserved or ordered.")
    matches = resolve_parts(conn, query, asset_model)
    if not matches:
        raise ServiceError("part_not_found", f"No part in the catalogue matches '{query}'.",
                           catalogue=[{"part_id": p["part_id"], "name": p["name"]} for p in _part_rows(conn)])
    return [_part_view(conn, p) for p in matches]


def _single_part(conn: sqlite3.Connection, part: str, asset_model: str | None) -> dict[str, Any]:
    matches = resolve_parts(conn, part, asset_model)
    if not matches:
        raise ServiceError("part_not_found", f"No part matches '{part}'.")
    if len(matches) > 1:
        raise ServiceError("part_ambiguous", f"'{part}' matches several parts; specify the part ID.",
                           candidates=[{"part_id": p["part_id"], "name": p["name"]} for p in matches])
    return matches[0]


def _default_work_order(conn: sqlite3.Connection, asset_id: str) -> str | None:
    row = conn.execute(
        "SELECT work_order_id FROM work_orders WHERE asset_id=? AND status NOT IN ('CLOSED','RESOLVED') ORDER BY priority, created_at LIMIT 1",
        (asset_id,),
    ).fetchone()
    return row["work_order_id"] if row else None


def resolve_work_order(conn: sqlite3.Connection, asset_id: str, raw: str | None) -> tuple[str | None, str | None]:
    """Accept a spoken/LLM work-order reference; fall back to the asset's open work order (with a note).
    Observed live: the LLM passed the asset ID 'C-204' as the work order."""
    default = _default_work_order(conn, asset_id)
    if not raw:
        return default, None
    wo = normalize_id(raw, "WO")
    if conn.execute("SELECT 1 FROM work_orders WHERE work_order_id=?", (wo,)).fetchone():
        return wo, None
    if default:
        return default, f"Work order '{raw}' not found; used {default}, the open work order for {asset_id}."
    raise ServiceError("work_order_not_found", f"No work order {raw} and no open work order for {asset_id}.")


def reserve_part(conn: sqlite3.Connection, ctx: SessionContext, part: str, quantity: int, work_order_id: str | None) -> dict[str, Any]:
    if flag_enabled(conn, "inventory_outage"):
        raise ServiceError("inventory_unavailable", "The inventory service is not responding (simulated outage). Nothing was reserved.")
    if quantity < 1 or quantity > 20:
        raise ServiceError("bad_quantity", "Quantity must be between 1 and 20.")
    asset = get_asset(conn, ctx.asset_id)
    p = _single_part(conn, part, asset["model"])
    wo, wo_note = resolve_work_order(conn, asset["asset_id"], work_order_id)
    existing = conn.execute(
        "SELECT * FROM reservations WHERE part_id=? AND IFNULL(work_order_id,'')=IFNULL(?,'') AND status='ACTIVE'", (p["part_id"], wo)
    ).fetchone()
    if existing:
        return {"reservation": row_to_dict(existing), "duplicate": True}
    available = p["quantity_on_hand"] - p["quantity_reserved"]
    if available < quantity:
        raise ServiceError("insufficient_stock", f"Only {available} of {p['name']} available; cannot reserve {quantity}.",
                           part_id=p["part_id"], available=available)
    rid = next_id(conn, "reservation", "RSV-", 3001)
    conn.execute(
        "INSERT INTO reservations VALUES (?,?,?,?,?,?,?)",
        (rid, p["part_id"], quantity, wo, ctx.session_id, "ACTIVE", utcnow()),
    )
    conn.execute("UPDATE parts SET quantity_reserved = quantity_reserved + ? WHERE part_id=?", (quantity, p["part_id"]))
    return {"reservation": row_to_dict(conn.execute("SELECT * FROM reservations WHERE reservation_id=?", (rid,)).fetchone()), "duplicate": False}


# --------------------------------------------------------------------------- procurement (approval-gated)

def create_procurement(conn: sqlite3.Connection, ctx: SessionContext, part: str, quantity: int,
                       work_order_id: str | None, reason: str | None) -> dict[str, Any]:
    if quantity < 1 or quantity > 20:
        raise ServiceError("bad_quantity", "Quantity must be between 1 and 20.")
    asset = get_asset(conn, ctx.asset_id)
    p = _single_part(conn, part, asset["model"])
    wo, wo_note = resolve_work_order(conn, asset["asset_id"], work_order_id)
    dedupe_key = f"{p['part_id']}|{wo or '-'}"
    existing = conn.execute(
        "SELECT * FROM procurement_requests WHERE dedupe_key=? AND status IN ('PENDING_APPROVAL','SUBMITTED') ORDER BY created_at DESC LIMIT 1",
        (dedupe_key,),
    ).fetchone()
    if existing:
        return {"request": get_procurement(conn, existing["request_id"]), "duplicate": True, "note": wo_note}
    rid = next_id(conn, "procurement", "PR-", 2001)
    watermark = conn.execute("SELECT IFNULL(max(id), 0) FROM transcript_events").fetchone()[0]
    conn.execute(
        """INSERT INTO procurement_requests(request_id, part_id, quantity, work_order_id, session_id, status, reason, dedupe_key,
           created_by, supplier, transcript_watermark, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (rid, p["part_id"], quantity, wo, ctx.session_id, "PENDING_APPROVAL", reason, dedupe_key, ctx.technician, p["supplier"],
         watermark, utcnow()),
    )
    return {"request": get_procurement(conn, rid), "duplicate": False, "note": wo_note}


def get_procurement(conn: sqlite3.Connection, request_id: str) -> dict[str, Any]:
    request_id = normalize_id(request_id, "PR")
    row = conn.execute(
        """SELECT pr.*, p.name AS part_name, p.lead_time_days FROM procurement_requests pr JOIN parts p ON p.part_id=pr.part_id
           WHERE upper(pr.request_id)=upper(?)""",
        (request_id.strip(),),
    ).fetchone()
    if row is None:
        raise ServiceError("request_not_found", f"No procurement request {request_id}.")
    return row_to_dict(row)  # type: ignore[return-value]


_AFFIRM = re.compile(r"\b(yes|yeah|yep|yup|approve|approved|confirm|confirmed|go ahead|submit|proceed|do it|sure|okay|ok|correct|move it|transfer it)\b", re.I)
_NEGATE = re.compile(r"\b(no|nope|don't|do not|dont|cancel|wait|hold on|hold off|stop|not yet|reject)\b", re.I)


def is_affirmative(text: str) -> bool:
    return bool(_AFFIRM.search(text)) and not _NEGATE.search(text)


def find_spoken_approval(conn: sqlite3.Connection, session_id: str | None, watermark: int) -> dict[str, Any] | None:
    """Return the technician's own transcribed 'yes' to the read-back of a draft, if any.

    This is the approval gate: the LLM cannot approve its own action. Only an utterance
    from the technician (relayed from Agora ASR transcripts by the console) or a console
    click counts. Ordering uses the append-only transcript_events log, not wall-clock time:
      1. `watermark` = last transcript event id when the draft was created;
      2. the agent must have spoken after that (the read-back);
      3. the technician's latest FINAL utterance after the read-back must be affirmative.
    A request like "order it and submit it" spoken before the read-back never counts.
    """
    if not session_id:
        return None
    readback = conn.execute(
        "SELECT min(id) FROM transcript_events WHERE session_id=? AND role='agent' AND id>?", (session_id, watermark)
    ).fetchone()[0]
    if readback is None:
        return None
    # The technician's latest reply after the read-back. ASR often splits one reply into several finals ("Yes." /
    # "Move it."; observed live 21 Nov), so the reply is every user final since the agent last spoke, read together:
    # "Yes." + "Move it." approves; "Yes." + "No, wait." does not.
    events = conn.execute(
        "SELECT * FROM transcript_events WHERE session_id=? AND id>? AND (role='agent' OR final=1) ORDER BY id DESC",
        (session_id, readback),
    ).fetchall()
    reply: list[sqlite3.Row] = []
    for ev in events:
        if ev["role"] == "agent":
            if reply:
                break
            continue  # agent speech after the reply (a filler while the tool runs) does not split it
        reply.append(ev)
    if not reply:
        return None
    reply.reverse()
    last = reply[-1]
    if is_affirmative(last["text"]):  # the latest words decide ("No, wait." then "Yes, submit it." approves)
        return dict(last)
    if _NEGATE.search(last["text"]):
        return None
    text = " ".join(r["text"] for r in reply)  # "Yes." then "Move it." / "Do the transfer." approves
    return {**dict(last), "text": text} if is_affirmative(text) else None


def add_transcript(conn: sqlite3.Connection, session_id: str, role: str, turn_id: str, text: str, final: bool) -> None:
    """Display copy (one row per turn, updated in place) + append-only event log (for approval ordering)."""
    now = utcnow()
    conn.execute(
        """INSERT INTO transcripts(session_id, ts, role, turn_id, text) VALUES (?,?,?,?,?)
           ON CONFLICT(session_id, role, turn_id) DO UPDATE SET text=excluded.text""",
        (session_id, now, role, turn_id, text),
    )
    conn.execute("INSERT INTO transcript_events(session_id, ts, role, turn_id, text, final) VALUES (?,?,?,?,?,?)",
                 (session_id, now, role, turn_id, text, int(final)))


def submit_procurement(conn: sqlite3.Connection, request_id: str, approver: str, via: str, evidence: str) -> dict[str, Any]:
    pr = get_procurement(conn, request_id)
    if pr["status"] == "SUBMITTED":
        return {"request": pr, "duplicate": True}
    if pr["status"] != "PENDING_APPROVAL":
        raise ServiceError("invalid_state", f"{pr['request_id']} is {pr['status']} and cannot be submitted.")
    now = utcnow()
    if flag_enabled(conn, "supplier_rejects"):
        conn.execute(
            "UPDATE procurement_requests SET status='REJECTED', approved_by=?, approval_via=?, approval_evidence=?, failure_reason=?, decided_at=? WHERE request_id=?",
            (approver, via, evidence, "Supplier portal rejected the order: account on credit hold (simulated).", now, pr["request_id"]),
        )
        return {"request": get_procurement(conn, pr["request_id"]), "duplicate": False}
    expected = (parse_ts(now) + timedelta(days=int(pr["lead_time_days"] or 3))).date().isoformat()
    supplier_ref = f"SO-{pr['request_id'].split('-')[1]}-{now[11:13]}{now[14:16]}"
    conn.execute(
        """UPDATE procurement_requests SET status='SUBMITTED', approved_by=?, approval_via=?, approval_evidence=?, decided_at=?,
           expected_by=?, supplier_ref=? WHERE request_id=?""",
        (approver, via, evidence, now, expected, supplier_ref, pr["request_id"]),
    )
    return {"request": get_procurement(conn, pr["request_id"]), "duplicate": False}


def reject_procurement(conn: sqlite3.Connection, request_id: str, by: str, via: str) -> dict[str, Any]:
    pr = get_procurement(conn, request_id)
    if pr["status"] != "PENDING_APPROVAL":
        raise ServiceError("invalid_state", f"{pr['request_id']} is {pr['status']}.")
    conn.execute(
        "UPDATE procurement_requests SET status='CANCELLED', approved_by=?, approval_via=?, decided_at=?, failure_reason='Declined by technician' WHERE request_id=?",
        (by, via, utcnow(), pr["request_id"]),
    )
    return get_procurement(conn, pr["request_id"])


# --------------------------------------------------------------------------- work orders

TRANSITIONS: dict[str, set[str]] = {
    "OPEN": {"IN_PROGRESS", "WAITING_PARTS", "ESCALATED"},
    "IN_PROGRESS": {"WAITING_PARTS", "ESCALATED", "RESOLVED"},
    "WAITING_PARTS": {"IN_PROGRESS", "ESCALATED"},
    "ESCALATED": {"IN_PROGRESS", "WAITING_PARTS"},
    "RESOLVED": {"IN_PROGRESS", "CLOSED"},
    "CLOSED": set(),
}
VOICE_FORBIDDEN = {"RESOLVED", "CLOSED"}


def update_work_order(conn: sqlite3.Connection, ctx: SessionContext, work_order_id: str, status: str | None,
                      note: str, via: str = "voice") -> dict[str, Any]:
    wo = work_order_with_log(conn, work_order_id)
    target = (status or wo["status"]).strip().upper().replace(" ", "_")
    if target not in TRANSITIONS:
        raise ServiceError("bad_status", f"Unknown status {status}. Allowed: {', '.join(TRANSITIONS)}.")
    if target != wo["status"] and target not in TRANSITIONS[wo["status"]]:
        raise ServiceError("bad_transition", f"{wo['work_order_id']} cannot move from {wo['status']} to {target}.",
                           allowed=sorted(TRANSITIONS[wo["status"]]))
    if via == "voice" and target in VOICE_FORBIDDEN and target != wo["status"]:
        raise ServiceError("needs_signoff", f"Marking a work order {target} needs supervisor sign-off in the console; it was not changed by voice.")
    if not note or not note.strip():
        raise ServiceError("note_required", "A note describing the update is required.")
    now = utcnow()
    conn.execute("UPDATE work_orders SET status=?, updated_at=? WHERE work_order_id=?", (target, now, wo["work_order_id"]))
    conn.execute(
        "INSERT INTO work_order_log(work_order_id, ts, author, status_from, status_to, note, session_id, via) VALUES (?,?,?,?,?,?,?,?)",
        (wo["work_order_id"], now, ctx.technician, wo["status"], target, note.strip(), ctx.session_id, via),
    )
    if target == "WAITING_PARTS":
        conn.execute("UPDATE assets SET status='DEGRADED' WHERE asset_id=?", (wo["asset_id"],))
    return work_order_with_log(conn, wo["work_order_id"])


def escalate(conn: sqlite3.Connection, ctx: SessionContext, work_order_id: str | None, severity: str, reason: str) -> dict[str, Any]:
    sev = severity.strip().lower()
    if sev not in {"low", "medium", "high"}:
        raise ServiceError("bad_severity", "Severity must be low, medium or high.")
    wo, _ = resolve_work_order(conn, ctx.asset_id, work_order_id)
    existing = conn.execute(
        "SELECT * FROM escalations WHERE IFNULL(work_order_id,'')=IFNULL(?,'') AND status='OPEN' AND session_id IS ?", (wo, ctx.session_id)
    ).fetchone()
    if existing:
        return {"escalation": row_to_dict(existing), "duplicate": True}
    eid = next_id(conn, "escalation", "ESC-", 4001)
    conn.execute("INSERT INTO escalations VALUES (?,?,?,?,?,?,?,?)", (eid, wo, ctx.asset_id, ctx.session_id, sev, reason, "OPEN", utcnow()))
    return {"escalation": row_to_dict(conn.execute("SELECT * FROM escalations WHERE escalation_id=?", (eid,)).fetchone()), "duplicate": False}


# --------------------------------------------------------------------------- evidence

_UNIT_ALIASES = {
    "a": "A", "amp": "A", "amps": "A", "ampere": "A", "amperes": "A",
    "pa": "Pa", "pascal": "Pa", "pascals": "Pa",
    "c": "°C", "°c": "°C", "degc": "°C", "deg c": "°C", "degrees": "°C", "degree": "°C", "celsius": "°C", "degrees celsius": "°C",
    "mm/s": "mm/s", "mms": "mm/s", "millimetres per second": "mm/s", "millimeters per second": "mm/s",
    "bar": "bar", "mm": "mm", "millimetres": "mm", "millimeters": "mm", "m/min": "m/min", "metres per minute": "m/min",
}


def norm_unit(unit: str | None) -> str:
    u = (unit or "").strip()
    return _UNIT_ALIASES.get(u.lower(), u)


def _fmt(v: float) -> str:
    return f"{v:g}"


def evaluate_reading(asset: dict[str, Any], reading: str, value: float, unit: str | None) -> dict[str, Any]:
    """Compare a reading with the limits configured for this machine (metadata.limits in its pack).
    Deterministic on purpose: the LLM misjudged '12.4 A vs a 10-13 A normal band' in a live run."""
    limits = (asset.get("metadata") or {}).get("limits") or []
    text = f" {reading.lower()} "
    best, best_len = None, 0
    for lim in limits:
        for alias in [lim["label"], *lim.get("aliases", [])]:
            if alias.lower() in text and len(alias) > best_len:
                best, best_len = lim, len(alias)
    if best is None:
        return {"status": "no_limit_configured", "say": "No limit is configured for this reading. Do not judge it; check the manual if asked.",
                "known_readings": [l["label"] for l in limits]}
    u = norm_unit(unit) or best["unit"]
    if u != best["unit"]:
        return {"status": "unit_mismatch", "limit": best, "say": f"The limit for {best['label']} is in {best['unit']}, not {u}. Ask the technician to confirm the unit."}
    lo_n, hi_n = (best.get("normal") or [None, None])
    lo_l, hi_l = best.get("limit_low"), best.get("limit_high")
    ref = f" (manual section {best['section']})" if best.get("section") else ""
    if hi_l is not None and value > hi_l:
        status, say = "out_of_limit", f"{_fmt(value)} {u} is above the {_fmt(hi_l)} {u} limit{ref}. {best.get('action_high', '')}".strip()
    elif lo_l is not None and value < lo_l:
        status, say = "out_of_limit", f"{_fmt(value)} {u} is below the {_fmt(lo_l)} {u} limit{ref}. {best.get('action_low', '')}".strip()
    elif lo_n is not None and hi_n is not None and not (lo_n <= value <= hi_n):
        side = "above" if value > hi_n else "below"
        status, say = "outside_normal", f"{_fmt(value)} {u} is {side} the normal {_fmt(lo_n)} to {_fmt(hi_n)} {u} band but within the limit{ref}. {best.get('note', '')}".strip()
    else:
        band = f"normal {_fmt(lo_n)} to {_fmt(hi_n)} {u}" if lo_n is not None else "the limit"
        status, say = "normal", f"{_fmt(value)} {u} is within {band}{ref}."
    return {"status": status, "reading": best["label"], "value": value, "unit": u, "say": say,
            "limit": {k: best.get(k) for k in ("normal", "limit_low", "limit_high", "section")}}


EVENT_KINDS = {
    "visual": ("visual_observation", "camera_model", "unverified"),
    "audio": ("audio_observation", "microphone_model", "unverified"),
    "technician_report": ("technician_statement", "technician", None),
    "hypothesis": ("hypothesis", "agent_inference", "open"),
    "open_question": ("open_question", "agent_inference", "open"),
}


def record_evidence(conn: sqlite3.Connection, *, session_id: str | None, asset_id: str, event_type: str, source_type: str,
                    title: str, detail: str | None = None, payload: dict | None = None, model_id: str | None = None,
                    status: str | None = None, verified_by: str | None = None, media_ref: str | None = None,
                    related_id: int | None = None) -> dict[str, Any]:
    cur = conn.execute(
        """INSERT INTO evidence(session_id, asset_id, ts, event_type, source_type, title, detail, payload_json, model_id, status, verified_by, media_ref, related_id)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (session_id, asset_id, utcnow(), event_type, source_type, title.strip()[:300], detail, json.dumps(payload or {}),
         model_id, status, verified_by, media_ref, related_id),
    )
    return row_to_dict(conn.execute("SELECT * FROM evidence WHERE id=?", (cur.lastrowid,)).fetchone())  # type: ignore[return-value]


def update_open_item(conn: sqlite3.Connection, ctx: SessionContext, event_id: int, status: str, note: str) -> dict[str, Any]:
    st = status.strip().lower().replace(" ", "_").replace("-", "_")
    if st not in {"confirmed", "ruled_out", "answered"}:
        raise ServiceError("bad_status", "Status must be confirmed, ruled_out or answered.")
    row = conn.execute("SELECT * FROM evidence WHERE id=?", (event_id,)).fetchone()
    if row is None or row["event_type"] not in ("hypothesis", "open_question"):
        raise ServiceError("not_open_item", f"Event {event_id} is not a hypothesis or open question.")
    conn.execute("UPDATE evidence SET status=?, verified_by=? WHERE id=?", (st, ctx.technician, event_id))
    record_evidence(conn, session_id=ctx.session_id, asset_id=row["asset_id"], event_type="technician_statement",
                    source_type="technician", title=f"Open item #{event_id} marked {st.replace('_', ' ')}", detail=note,
                    related_id=event_id, verified_by=ctx.technician)
    return row_to_dict(conn.execute("SELECT * FROM evidence WHERE id=?", (event_id,)).fetchone())  # type: ignore[return-value]


# --------------------------------------------------------------------------- tool audit

def log_tool_action(conn: sqlite3.Connection, session_id: str | None, tool: str, caller: str, args: dict, result: Any,
                    status: str, duration_ms: int) -> int:
    cur = conn.execute(
        "INSERT INTO tool_actions(session_id, ts, tool_name, caller, input_json, result_json, status, duration_ms) VALUES (?,?,?,?,?,?,?,?)",
        (session_id, utcnow(), tool, caller, json.dumps(args, default=str), json.dumps(result, default=str), status, duration_ms),
    )
    return int(cur.lastrowid)


# --------------------------------------------------------------------------- handoff

READ_TOOLS = {"get_asset_history", "get_open_work_orders", "get_previous_handoff", "search_maintenance_manual", "check_inventory", "get_open_items",
              "track_shipment", "get_training_module"}


def compose_handoff(conn: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    s = conn.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
    if s is None:
        raise ServiceError("session_not_found", f"No session {session_id}.")
    asset = get_asset(conn, s["asset_id"])
    aid = asset["asset_id"]
    prev = latest_handoff(conn, aid, exclude_session=session_id)

    wos = open_work_orders(conn, aid)
    primary_wo = wos[0] if wos else None
    if primary_wo is None:
        row = conn.execute("SELECT work_order_id FROM work_orders WHERE asset_id=? ORDER BY updated_at DESC LIMIT 1", (aid,)).fetchone()
        primary_wo = work_order_with_log(conn, row["work_order_id"]) if row else None

    ev = rows_to_dicts(conn.execute("SELECT * FROM evidence WHERE session_id=? ORDER BY ts", (session_id,)).fetchall())
    observations = [
        {"event_id": e["id"], "ts": e["ts"], "text": e["title"], "detail": e["detail"], "source": e["source_type"],
         "model_id": e["model_id"], "status": e["status"], "media_ref": e["media_ref"]}
        for e in ev if e["event_type"] in ("visual_observation", "audio_observation", "technician_statement")
    ]

    completed: list[dict[str, Any]] = []
    failed_or_pending: list[dict[str, Any]] = []
    parts: list[dict[str, Any]] = []
    for pr in rows_to_dicts(conn.execute(
            "SELECT pr.*, p.name AS part_name FROM procurement_requests pr JOIN parts p ON p.part_id=pr.part_id WHERE pr.session_id=? ORDER BY created_at",
            (session_id,)).fetchall()):
        item = {"text": f"Procurement {pr['request_id']}: {pr['quantity']} x {pr['part_name']} ({pr['part_id']}) for {pr['work_order_id']}",
                "ref": pr["request_id"], "status": pr["status"]}
        if pr["status"] == "SUBMITTED":
            completed.append({**item, "verified": True,
                              "detail": f"Submitted to {pr['supplier']}, ref {pr['supplier_ref']}, expected by {pr['expected_by']}. Approved by {pr['approved_by']} via {pr['approval_via']}."})
            parts.append({"part_id": pr["part_id"], "name": pr["part_name"], "state": f"ordered, expected by {pr['expected_by']}", "ref": pr["request_id"]})
        else:
            failed_or_pending.append({**item, "detail": pr["failure_reason"] or "Awaiting technician approval; not submitted."})
            parts.append({"part_id": pr["part_id"], "name": pr["part_name"], "state": pr["status"].lower().replace("_", " "), "ref": pr["request_id"]})
    for r in rows_to_dicts(conn.execute(
            "SELECT r.*, p.name AS part_name FROM reservations r JOIN parts p ON p.part_id=r.part_id WHERE r.session_id=?", (session_id,)).fetchall()):
        completed.append({"text": f"Reserved {r['quantity']} x {r['part_name']} ({r['part_id']})", "ref": r["reservation_id"], "verified": True})
        parts.append({"part_id": r["part_id"], "name": r["part_name"], "state": "reserved in stores", "ref": r["reservation_id"]})
    for log in rows_to_dicts(conn.execute("SELECT * FROM work_order_log WHERE session_id=? ORDER BY ts", (session_id,)).fetchall()):
        change = f"{log['status_from']} -> {log['status_to']}" if log["status_from"] != log["status_to"] else "note added"
        completed.append({"text": f"{log['work_order_id']} {change}: {log['note']}", "ref": log["work_order_id"], "verified": True})
    for esc in rows_to_dicts(conn.execute("SELECT * FROM escalations WHERE session_id=?", (session_id,)).fetchall()):
        completed.append({"text": f"Escalated ({esc['severity']}) {esc['work_order_id']}: {esc['reason']}", "ref": esc["escalation_id"], "verified": True})
    # warehouse: stock transfers (done ones are posted to the ERP)
    for t in rows_to_dicts(conn.execute(
            "SELECT t.*, p.name AS part_name FROM stock_transfers t JOIN parts p ON p.part_id=t.part_id WHERE t.session_id=? ORDER BY created_at",
            (session_id,)).fetchall()):
        item = {"text": f"Stock transfer {t['transfer_id']}: {t['quantity']} x {t['part_name']} from {t['from_location']} to {t['to_location']}", "ref": t["transfer_id"], "status": t["status"]}
        if t["status"] == "DONE":
            completed.append({**item, "verified": True, "detail": f"Posted to the ERP as {t['erp_ref']}. Confirmed by {t['confirmed_by']} via {t['confirmation_via']}."})
        else:
            failed_or_pending.append({**item, "status": "PENDING_APPROVAL" if t["status"] == "PENDING_CONFIRMATION" else t["status"],
                                      "detail": t["failure_reason"] or ("Awaiting confirmation; nothing was moved." if t["status"] == "PENDING_CONFIRMATION" else t["status"].lower())})
    # training: learning records updated in this session
    for lr in rows_to_dicts(conn.execute("SELECT * FROM learning_records WHERE last_session_id=?", (session_id,)).fetchall()):
        completed.append({"text": f"Learning record: {lr['trainee']}, {lr['title']}: {lr['score']}%, {lr['status'].replace('_', ' ').lower()}",
                          "ref": lr["module_id"], "verified": True})
    follow_ups = rows_to_dicts(conn.execute("SELECT * FROM follow_ups WHERE session_id=? ORDER BY created_at", (session_id,)).fetchall())

    consulted: dict[str, dict[str, Any]] = {}
    for ta in rows_to_dicts(conn.execute("SELECT * FROM tool_actions WHERE session_id=? ORDER BY ts", (session_id,)).fetchall()):
        if ta["status"] == "error":
            msg = (ta.get("result") or {}).get("message") if isinstance(ta.get("result"), dict) else None
            failed_or_pending.append({"text": f"{ta['tool_name']} failed", "detail": msg, "ref": f"tool#{ta['id']}"})
        elif ta["tool_name"] in READ_TOOLS:
            key = f"{ta['tool_name']}:{json.dumps(ta.get('input'), sort_keys=True)}"
            consulted[key] = {"tool": ta["tool_name"], "input": ta.get("input"), "ts": ta["ts"]}
            if ta["tool_name"] == "check_inventory" and isinstance(ta.get("result"), dict):
                for m in ta["result"].get("matches", []):
                    if not m.get("in_stock") and not any(p["part_id"] == m["part_id"] for p in parts):
                        parts.append({"part_id": m["part_id"], "name": m["name"], "state": "out of stock at check time", "ref": None})

    loops = open_items(conn, aid)
    resolved_here = rows_to_dicts(conn.execute(
        """SELECT e.* FROM evidence e WHERE e.asset_id=? AND e.event_type IN ('hypothesis','open_question') AND e.status IN ('confirmed','ruled_out','answered')
           AND e.id IN (SELECT related_id FROM evidence WHERE session_id=? AND related_id IS NOT NULL)""",
        (aid, session_id)).fetchall())

    manual_refs = sorted({
        m["chunk_id"]
        for ta in rows_to_dicts(conn.execute("SELECT * FROM tool_actions WHERE session_id=? AND tool_name='search_maintenance_manual' AND status='ok'", (session_id,)).fetchall())
        for m in ((ta.get("result") or {}).get("sections", []) if isinstance(ta.get("result"), dict) else [])
    })

    safety_notes = (asset.get("metadata") or {}).get("safety_notes") or []
    safety = safety_notes[0] if safety_notes else "Follow the site isolation procedure."
    steps: list[str] = []
    for p in parts:
        if p["state"].startswith("ordered"):
            steps.append(f"Fit {p['name']} when {p['ref']} arrives ({p['state']}). {safety} (suggestion)")
        elif p["state"] == "pending approval":
            steps.append(f"Decide on {p['ref']}: it was drafted but never approved. (suggestion)")
    for f in follow_ups:
        steps.append(f"Follow-up {f['follow_up_id']} ({f['assignee']}, due {f['due_date'] or f['due_text'] or 'no date'}): {f['title']} (scheduled)")
    for loop in loops:
        steps.append(f"Close open loop #{loop['id']}: {loop['title']} (suggestion)")
    if primary_wo and primary_wo["status"] == "ESCALATED":
        steps.append("Follow up with the shift supervisor on the escalation. (suggestion)")

    wo_view = ({"work_order_id": primary_wo["work_order_id"], "status": primary_wo["status"], "priority": primary_wo["priority"],
                "title": primary_wo["title"]} if primary_wo else None)
    headline_bits = []
    if wo_view:
        headline_bits.append(f"{wo_view['work_order_id']} is {wo_view['status'].replace('_', ' ').lower()}")
    vis = [o for o in observations if o["source"] == "camera_model"]
    if vis:
        headline_bits.append(f"camera showed: {vis[-1]['text']}")
    ordered = [p for p in parts if p["state"].startswith("ordered")]
    if ordered:
        headline_bits.append(f"{ordered[0]['name']} ordered ({ordered[0]['ref']}, {ordered[0]['state'].replace('ordered, ', '')})")
    headline_bits.append(f"{len(loops)} open loop{'s' if len(loops) != 1 else ''}")
    headline = "; ".join(headline_bits) + "."

    spoken = [f"Handoff for {asset['name']} from {s['technician']}."]
    if wo_view:
        spoken.append(f"Work order {wo_view['work_order_id']} is now {wo_view['status'].replace('_', ' ').lower()}.")
    if vis:
        spoken.append(f"Camera observation, not a diagnosis: {vis[-1]['text']}.")
    for c in completed[:3]:
        spoken.append(f"Done and verified: {c['text']}.")
    for f in failed_or_pending[:2]:
        spoken.append(f"Not completed: {f['text']}.")
    if follow_ups:
        spoken.append(f"Follow-up scheduled: {follow_ups[0]['title']}, due {follow_ups[0]['due_date'] or follow_ups[0]['due_text'] or 'no date'}.")
    if loops:
        spoken.append(f"{len(loops)} open loops remain, including: {loops[0]['title']}.")

    from .packs import PackError, get_task
    try:
        t = get_task(s["task_id"] if "task_id" in s.keys() else None)
        task_view = {"id": t["id"], "label": t["label"]}
    except PackError:
        task_view = {"id": s["task_id"], "label": s["task_id"]}
    if task_view["id"] != "troubleshoot":
        spoken.insert(1, f"Session type: {task_view['label']}.")

    report = {
        "schema": "shifttrace.handoff/v1",
        "asset": {"asset_id": aid, "name": asset["name"], "model": asset["model"], "location": asset["location"]},
        "session": {"session_id": session_id, "technician": s["technician"], "shift": s["shift_label"],
                    "started_at": s["started_at"], "ended_at": s["ended_at"]},
        "task": task_view,
        "headline": headline,
        "work_order": wo_view,
        "carried_over_from": prev["handoff_id"] if prev else None,
        "observations": observations,
        "records_consulted": list(consulted.values()),
        "actions_completed": completed,
        "actions_failed_or_pending": failed_or_pending,
        "parts": parts,
        "ruled_out": [{"event_id": r["id"], "text": r["title"], "status": r["status"]} for r in resolved_here if r["status"] == "ruled_out"],
        "confirmed": [{"event_id": r["id"], "text": r["title"], "status": r["status"]} for r in resolved_here if r["status"] != "ruled_out"],
        "open_loops": [{"event_id": l["id"], "text": l["title"], "type": l["event_type"], "raised_by": l.get("raised_by_technician"), "since": l["ts"]} for l in loops],
        "suggested_next_steps": steps,
        "follow_ups": [{"follow_up_id": f["follow_up_id"], "title": f["title"], "due": f["due_date"] or f["due_text"], "assignee": f["assignee"]} for f in follow_ups],
        "manual_refs": manual_refs,
        "spoken_summary": " ".join(spoken),
        "generated_by": "shifttrace deterministic composer (from persisted records only)",
    }
    existing = conn.execute("SELECT handoff_id FROM handoffs WHERE session_id=?", (session_id,)).fetchone()
    now = utcnow()
    if existing:
        hid = existing["handoff_id"]
        conn.execute("UPDATE handoffs SET report_json=?, created_at=? WHERE handoff_id=?", (json.dumps(report), now, hid))
    else:
        hid = _handoff_id(conn)
        conn.execute("INSERT INTO handoffs VALUES (?,?,?,?,?,?,?)", (hid, aid, session_id, now, s["technician"], json.dumps(report), "PUBLISHED"))
        record_evidence(conn, session_id=session_id, asset_id=aid, event_type="system_record", source_type="cmms",
                        title=f"Shift handoff {hid} created", detail=headline, payload={"handoff_id": hid})
    conn.execute("UPDATE sessions SET summary=? WHERE session_id=?", (headline, session_id))
    return row_to_dict(conn.execute("SELECT * FROM handoffs WHERE handoff_id=?", (hid,)).fetchone())  # type: ignore[return-value]


def _handoff_id(conn: sqlite3.Connection) -> str:
    raw = next_id(conn, "handoff", "", 43)
    return f"H-{int(raw):04d}"
