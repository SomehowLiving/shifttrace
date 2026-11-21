"""Deterministic demo seed, loaded from data packs (demo_data/packs/*/pack.json).

All data is synthetic. Pack timestamps are relative ("ago:17h") so the story always reads
"last night's shift" no matter when the demo is reset. Which packs load: SHIFTTRACE_PACKS (default all).

Run:  uv run python -m app.seed
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .config import settings
from .db import connect, init_schema
from .packs import load_pack, selected_pack_ids

ASSET_COLS = ("asset_id", "name", "asset_type", "manufacturer", "model", "serial_no", "location", "status", "criticality")
WO_COLS = ("work_order_id", "asset_id", "title", "description", "priority", "status", "assigned_to", "created_at", "updated_at")
LOG_COLS = ("work_order_id", "ts", "author", "status_from", "status_to", "note", "session_id", "via")
SESSION_COLS = ("session_id", "asset_id", "technician", "shift_label", "started_at", "ended_at", "status", "summary", "task_id")
EV_COLS = ("session_id", "asset_id", "ts", "event_type", "source_type", "title", "detail", "model_id", "status", "verified_by", "media_ref")
PR_COLS = ("request_id", "part_id", "quantity", "work_order_id", "session_id", "status", "reason", "dedupe_key", "created_by", "approved_by",
           "approval_via", "approval_evidence", "supplier", "expected_by", "supplier_ref", "failure_reason", "transcript_watermark", "created_at", "decided_at")
TR_COLS = ("transfer_id", "part_id", "quantity", "from_location", "to_location", "reason", "status", "session_id", "asset_id", "created_by",
           "confirmed_by", "confirmation_via", "confirmation_evidence", "erp_ref", "failure_reason", "transcript_watermark", "created_at", "decided_at")
PART_COLS = ("part_id", "name", "description", "quantity_on_hand", "quantity_reserved", "location", "reorder_threshold",
             "lead_time_days", "supplier", "compatible_models")


def _insert(conn, table: str, cols: tuple[str, ...], row: dict[str, Any], extra: dict[str, Any] | None = None) -> None:
    values = {c: row.get(c) for c in cols}
    values.update(extra or {})
    names = list(values)
    conn.execute(f"INSERT INTO {table}({','.join(names)}) VALUES ({','.join('?' * len(names))})", [values[n] for n in names])


def reset_database() -> None:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        p = settings.db_path.with_name(settings.db_path.name + suffix)
        if p.exists():
            p.unlink()
    conn = connect()
    try:
        init_schema(conn)
        seed(conn)
        conn.commit()
    finally:
        conn.close()


def seed_pack(conn, pack: dict[str, Any]) -> None:
    for a in pack.get("assets", []):
        _insert(conn, "assets", ASSET_COLS, a, {"metadata_json": json.dumps({**a.get("metadata", {}), "pack": pack["id"]})})
    for p in pack.get("parts", []):
        if conn.execute("SELECT 1 FROM parts WHERE part_id=?", (p["part_id"],)).fetchone():
            continue  # shared consumables (e.g. grease) may appear in several packs
        locs = p.get("locations") or {}
        on_hand = sum(locs.values()) if locs else p.get("quantity_on_hand", 0)
        _insert(conn, "parts", PART_COLS, {"quantity_reserved": 0, "reorder_threshold": 0, **p, "quantity_on_hand": on_hand,
                                            "location": p.get("location") or (next(iter(locs)) if locs else None)})
        for loc, qty in locs.items():  # per-location stock (warehouse packs): enables stock transfers
            conn.execute("INSERT INTO stock_levels VALUES (?,?,?)", (p["part_id"], loc, qty))
    for sh in pack.get("shipments", []):
        conn.execute("INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                     (sh["shipment_id"], sh.get("asset_id"), sh["direction"], sh.get("carrier"), sh.get("carrier_ref"), sh["status"],
                      sh.get("origin"), sh.get("destination"), sh.get("eta"), json.dumps(sh.get("items") or []), sh.get("last_event"), sh["updated_at"]))
        for ev in sh.get("events", []):
            conn.execute("INSERT INTO shipment_events(shipment_id, ts, location, status, note) VALUES (?,?,?,?,?)",
                         (sh["shipment_id"], ev["ts"], ev.get("location"), ev.get("status"), ev.get("note")))
    # Earlier business records, so the console has history before the first live session (all synthetic).
    for pr in pack.get("procurement", []):
        _insert(conn, "procurement_requests", PR_COLS, {"dedupe_key": f"{pr['part_id']}|{pr.get('work_order_id') or '-'}", "transcript_watermark": 0, **pr})
    for r in pack.get("reservations", []):
        _insert(conn, "reservations", ("reservation_id", "part_id", "quantity", "work_order_id", "session_id", "status", "created_at"), r)
        if r["status"] == "ACTIVE":
            conn.execute("UPDATE parts SET quantity_reserved=quantity_reserved+? WHERE part_id=?", (r["quantity"], r["part_id"]))
    for e in pack.get("escalations", []):
        _insert(conn, "escalations", ("escalation_id", "work_order_id", "asset_id", "session_id", "severity", "reason", "status", "created_at"), e)
    for t in pack.get("transfers", []):
        _insert(conn, "stock_transfers", TR_COLS, {"transcript_watermark": 0, **t})
    for e in pack.get("erp_postings", []):
        conn.execute("INSERT INTO erp_postings VALUES (?,?,?,?,?,?)", (e["erp_ref"], e["ts"], e["doc_type"], e["doc_ref"], json.dumps(e.get("payload") or {}), e.get("status", "POSTED")))
    for f in pack.get("follow_ups", []):
        _insert(conn, "follow_ups", ("follow_up_id", "title", "due_text", "due_date", "assignee", "asset_id", "session_id", "created_by", "status", "created_at"),
                {**f, "due_date": (f.get("due_date") or "")[:10] or None})
    for lr in pack.get("learning_records", []):
        conn.execute("INSERT INTO learning_records VALUES (?,?,?,?,?,?,?,?,?)",
                     (lr["trainee"], lr["module_id"], lr.get("title"), lr.get("asset_id"), lr["status"], lr.get("score"), lr.get("attempts", 1),
                      lr.get("last_session_id"), lr["updated_at"]))
    for w in pack.get("work_orders", []):
        _insert(conn, "work_orders", WO_COLS, w)
    for log in pack.get("work_order_log", []):
        _insert(conn, "work_order_log", LOG_COLS, {"via": "cmms", **log})
    for s in pack.get("sessions", []):
        _insert(conn, "sessions", SESSION_COLS, s)
    session_asset = {s["session_id"]: s["asset_id"] for s in pack.get("sessions", [])}
    for e in pack.get("evidence", []):
        asset = e.get("asset_id") or session_asset.get(e.get("session_id"))
        _insert(conn, "evidence", EV_COLS, {**e, "asset_id": asset}, {"payload_json": json.dumps(e.get("payload") or {})})
    for chunk in pack["_manual_chunks"]:
        conn.execute("INSERT INTO manual_chunks VALUES (?,?,?,?,?)", chunk)
    for h in pack.get("handoffs", []):
        conn.execute("INSERT INTO handoffs VALUES (?,?,?,?,?,?,?)",
                     (h["handoff_id"], h["asset_id"], h.get("session_id"), h["created_at"], h["created_by"],
                      json.dumps(h["report"]), h.get("status", "PUBLISHED")))


def seed(conn, pack_ids: list[str] | None = None) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    for pid in pack_ids or selected_pack_ids():
        seed_pack(conn, load_pack(pid, now))
    conn.executemany(
        "INSERT INTO counters(name, value) VALUES (?,?)",
        [("session", 1000), ("handoff", 42), ("procurement", 2000), ("reservation", 3000), ("escalation", 4000),
         ("follow_up", 5000), ("transfer", 6000), ("erp", 70000)],
    )
    conn.executemany("INSERT INTO demo_flags VALUES (?,?)", [("inventory_outage", 0), ("supplier_rejects", 0), ("integration_local_receiver", 0)])


if __name__ == "__main__":
    reset_database()
    print(f"Seeded {settings.db_path}")
