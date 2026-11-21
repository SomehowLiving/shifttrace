"""Configuration-driven scenarios: data packs (sites/machines) and task profiles.

A *pack* (demo_data/packs/<id>/pack.json + manual .md files) holds the synthetic machines, their manuals,
parts, work orders, previous sessions, evidence and handoffs for one site or use case. Which packs are loaded
is set by SHIFTTRACE_PACKS (comma-separated ids, default: all).

A *task* (demo_data/tasks.json, plus optional "tasks" in a pack) is what the technician is doing in a session:
troubleshooting, preventive maintenance, an inspection round, a read-only briefing... It sets the agent's goal,
procedure, greeting and optionally restricts which tools it may call. An asset lists the tasks it offers in
metadata.tasks (first = default).

Timestamps in a pack are relative, written "ago:3d2h15m", so the story always reads "last night" after a reset.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import PROJECT_DIR

PACKS_DIR = Path(os.getenv("SHIFTTRACE_PACKS_DIR", str(PROJECT_DIR / "demo_data" / "packs")))
TASKS_FILE = PROJECT_DIR / "demo_data" / "tasks.json"
_AGO = re.compile(r"^(ago|in):(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?$")
SECTION = re.compile(r"^## (\d+\.\d+) (.+?)\n(.*?)(?=^## |\Z)", re.S | re.M)


class PackError(ValueError):
    pass


def _resolve_times(node: Any, now: datetime) -> Any:
    if isinstance(node, str):
        m = _AGO.match(node)
        if m:
            d, h, mi = (int(x or 0) for x in m.groups()[1:])
            delta = timedelta(days=d, hours=h, minutes=mi)
            when = now - delta if m.group(1) == "ago" else now + delta  # "in:3h" = future (ETAs, due dates)
            return when.isoformat(timespec="seconds").replace("+00:00", "Z")
        return node
    if isinstance(node, dict):
        return {k: _resolve_times(v, now) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_times(v, now) for v in node]
    return node


def available_pack_ids() -> list[str]:
    if not PACKS_DIR.exists():
        return []
    return sorted(p.name for p in PACKS_DIR.iterdir() if (p / "pack.json").exists())


def selected_pack_ids() -> list[str]:
    raw = os.getenv("SHIFTTRACE_PACKS", "all").strip()
    avail = available_pack_ids()
    if raw in ("", "all", "*"):
        return avail
    wanted = [x.strip() for x in raw.split(",") if x.strip()]
    missing = [w for w in wanted if w not in avail]
    if missing:
        raise PackError(f"SHIFTTRACE_PACKS names unknown pack(s) {missing}; available: {avail}")
    return wanted


def read_pack(pack_id: str) -> dict[str, Any]:
    path = PACKS_DIR / pack_id / "pack.json"
    pack = json.loads(path.read_text(encoding="utf-8"))
    pack.setdefault("id", pack_id)
    pack["_dir"] = str(path.parent)
    return pack


def load_pack(pack_id: str, now: datetime | None = None) -> dict[str, Any]:
    """Pack with relative times resolved and manual sections parsed."""
    now = now or datetime.now(timezone.utc).replace(microsecond=0)
    pack = _resolve_times(read_pack(pack_id), now)
    chunks = []
    for m in pack.get("manuals", []):
        text = (Path(pack["_dir"]) / m["file"]).read_text(encoding="utf-8")
        for sec in SECTION.finditer(text):
            chunks.append((f"{m['prefix']}-{sec.group(1)}", m["model"], sec.group(1), sec.group(2).strip(), sec.group(3).strip()))
        if not chunks:
            raise PackError(f"{pack_id}: manual {m['file']} has no '## N.M Title' sections")
    pack["_manual_chunks"] = chunks
    return pack


def pack_summaries() -> list[dict[str, Any]]:
    out = []
    selected = set(selected_pack_ids())
    for pid in available_pack_ids():
        p = read_pack(pid)
        out.append({"id": pid, "name": p.get("name", pid), "description": p.get("description", ""),
                    "loaded": pid in selected, "assets": [a["asset_id"] for a in p.get("assets", [])]})
    return out


# ----------------------------------------------------------------------------- tasks

@lru_cache(maxsize=1)
def _task_table() -> dict[str, dict[str, Any]]:
    from .mcp_server import TOOL_NAMES

    tasks: dict[str, dict[str, Any]] = {}
    sources = [json.loads(TASKS_FILE.read_text(encoding="utf-8")).get("tasks", [])]
    for pid in available_pack_ids():
        sources.append(read_pack(pid).get("tasks", []))
    for src in sources:
        for t in src:
            for key in ("id", "label", "goal"):
                if not t.get(key):
                    raise PackError(f"task {t.get('id')!r} is missing '{key}'")
            bad = [x for x in t.get("tools") or [] if x not in TOOL_NAMES]
            if bad:
                raise PackError(f"task {t['id']} lists unknown tools {bad}")
            tasks[t["id"]] = {"procedure": [], "summary": "", "tools": None, "greeting": None, **t}
    if not tasks:
        raise PackError(f"no tasks defined in {TASKS_FILE}")
    return tasks


def reload_tasks() -> None:
    _task_table.cache_clear()


def all_tasks() -> list[dict[str, Any]]:
    return list(_task_table().values())


def get_task(task_id: str | None) -> dict[str, Any]:
    table = _task_table()
    if task_id and task_id in table:
        return table[task_id]
    if task_id:
        raise PackError(f"unknown task {task_id!r}; known: {sorted(table)}")
    return table.get("troubleshoot") or next(iter(table.values()))


def tasks_for_asset(asset: dict[str, Any]) -> list[dict[str, Any]]:
    table = _task_table()
    ids = (asset.get("metadata") or {}).get("tasks") or list(table)
    return [table[i] for i in ids if i in table]


def default_task_id(asset: dict[str, Any]) -> str:
    offered = tasks_for_asset(asset)
    return offered[0]["id"] if offered else get_task(None)["id"]


def allowed_tools(task: dict[str, Any]) -> list[str]:
    """A task's explicit list, else the core tools. Domain tools (warehouse, training) are opt-in per task so a
    troubleshooting agent is not offered stock transfers or quizzes."""
    from .mcp_server import CORE_TOOLS

    return list(task["tools"]) if task.get("tools") else list(CORE_TOOLS)
