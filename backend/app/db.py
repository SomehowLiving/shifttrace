"""SQLite storage. One file, WAL mode, short-lived connections."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    manufacturer TEXT,
    model TEXT,
    serial_no TEXT,
    location TEXT,
    status TEXT NOT NULL,
    criticality TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id),
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_to TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS work_order_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id TEXT NOT NULL REFERENCES work_orders(work_order_id),
    ts TEXT NOT NULL,
    author TEXT NOT NULL,
    status_from TEXT,
    status_to TEXT,
    note TEXT,
    session_id TEXT,
    via TEXT NOT NULL DEFAULT 'cmms'
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id),
    technician TEXT NOT NULL,
    shift_label TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL,
    agent_id TEXT,
    channel TEXT,
    agent_config_json TEXT,
    summary TEXT,
    task_id TEXT
);
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    asset_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    detail TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    model_id TEXT,
    status TEXT,
    verified_by TEXT,
    media_ref TEXT,
    related_id INTEGER
);
CREATE TABLE IF NOT EXISTS parts (
    part_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    quantity_on_hand INTEGER NOT NULL,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    location TEXT,
    reorder_threshold INTEGER NOT NULL DEFAULT 0,
    lead_time_days INTEGER,
    supplier TEXT,
    compatible_models TEXT
);
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id TEXT PRIMARY KEY,
    part_id TEXT NOT NULL REFERENCES parts(part_id),
    quantity INTEGER NOT NULL,
    work_order_id TEXT,
    session_id TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS procurement_requests (
    request_id TEXT PRIMARY KEY,
    part_id TEXT NOT NULL REFERENCES parts(part_id),
    quantity INTEGER NOT NULL,
    work_order_id TEXT,
    session_id TEXT,
    status TEXT NOT NULL,
    reason TEXT,
    dedupe_key TEXT NOT NULL,
    created_by TEXT,
    approved_by TEXT,
    approval_via TEXT,
    approval_evidence TEXT,
    supplier TEXT,
    expected_by TEXT,
    supplier_ref TEXT,
    failure_reason TEXT,
    transcript_watermark INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    decided_at TEXT
);
CREATE TABLE IF NOT EXISTS escalations (
    escalation_id TEXT PRIMARY KEY,
    work_order_id TEXT,
    asset_id TEXT NOT NULL,
    session_id TEXT,
    severity TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tool_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    ts TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    caller TEXT NOT NULL,
    input_json TEXT NOT NULL,
    result_json TEXT,
    status TEXT NOT NULL,
    duration_ms INTEGER
);
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    role TEXT NOT NULL,
    turn_id TEXT,
    text TEXT NOT NULL,
    UNIQUE(session_id, role, turn_id)
);
CREATE TABLE IF NOT EXISTS transcript_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    role TEXT NOT NULL,
    turn_id TEXT,
    text TEXT NOT NULL,
    final INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS handoffs (
    handoff_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    session_id TEXT,
    created_at TEXT NOT NULL,
    created_by TEXT,
    report_json TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS manual_chunks (
    chunk_id TEXT PRIMARY KEY,
    asset_model TEXT NOT NULL,
    section TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS demo_flags (
    flag TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS stock_levels (
    part_id TEXT NOT NULL REFERENCES parts(part_id),
    location TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (part_id, location)
);
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id TEXT PRIMARY KEY,
    asset_id TEXT,
    direction TEXT NOT NULL,
    carrier TEXT,
    carrier_ref TEXT,
    status TEXT NOT NULL,
    origin TEXT,
    destination TEXT,
    eta TEXT,
    items_json TEXT,
    last_event TEXT,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shipment_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    location TEXT,
    status TEXT,
    note TEXT
);
CREATE TABLE IF NOT EXISTS stock_transfers (
    transfer_id TEXT PRIMARY KEY,
    part_id TEXT NOT NULL REFERENCES parts(part_id),
    quantity INTEGER NOT NULL,
    from_location TEXT NOT NULL,
    to_location TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL,
    session_id TEXT,
    asset_id TEXT,
    created_by TEXT,
    confirmed_by TEXT,
    confirmation_via TEXT,
    confirmation_evidence TEXT,
    erp_ref TEXT,
    failure_reason TEXT,
    transcript_watermark INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    decided_at TEXT
);
CREATE TABLE IF NOT EXISTS erp_postings (
    erp_ref TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    doc_ref TEXT NOT NULL,
    payload_json TEXT,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS follow_ups (
    follow_up_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    due_text TEXT,
    due_date TEXT,
    assignee TEXT,
    asset_id TEXT,
    session_id TEXT,
    created_by TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS training_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    trainee TEXT NOT NULL,
    module_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    answer TEXT NOT NULL,
    result TEXT NOT NULL,
    matched_json TEXT,
    ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS learning_records (
    trainee TEXT NOT NULL,
    module_id TEXT NOT NULL,
    title TEXT,
    asset_id TEXT,
    status TEXT NOT NULL,
    score INTEGER,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_session_id TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (trainee, module_id)
);
CREATE TABLE IF NOT EXISTS integration_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    event_type TEXT NOT NULL,
    ref TEXT,
    summary TEXT,
    payload_json TEXT,
    session_id TEXT,
    asset_id TEXT
);
CREATE TABLE IF NOT EXISTS integration_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    connector TEXT NOT NULL,
    target TEXT,
    status TEXT NOT NULL,
    http_status INTEGER,
    detail TEXT,
    attempts INTEGER,
    ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS integration_received (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    event_type TEXT,
    signature_valid INTEGER NOT NULL,
    body_json TEXT
);
CREATE TABLE IF NOT EXISTS usage_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT
);
CREATE TABLE IF NOT EXISTS site_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS counters (
    name TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def connect() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


MIGRATIONS = [("sessions", "task_id", "TEXT")]  # columns added after the first release; old DBs get them on start


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for table, col, typ in MIGRATIONS:
        if col not in {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")


def next_id(conn: sqlite3.Connection, name: str, prefix: str, start: int) -> str:
    row = conn.execute("SELECT value FROM counters WHERE name=?", (name,)).fetchone()
    value = (row["value"] + 1) if row else start
    conn.execute(
        "INSERT INTO counters(name, value) VALUES(?, ?) ON CONFLICT(name) DO UPDATE SET value=excluded.value",
        (name, value),
    )
    return f"{prefix}{value}"


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    d = dict(row)
    for key in list(d.keys()):
        if key.endswith("_json") and isinstance(d[key], str):
            try:
                d[key[:-5]] = json.loads(d[key])
            except json.JSONDecodeError:
                d[key[:-5]] = None
            del d[key]
    return d


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [row_to_dict(r) for r in rows]  # type: ignore[misc]


def flag_enabled(conn: sqlite3.Connection, flag: str) -> bool:
    row = conn.execute("SELECT enabled FROM demo_flags WHERE flag=?", (flag,)).fetchone()
    return bool(row and row["enabled"])
