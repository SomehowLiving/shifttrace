"""Agent quality: the improvement loop, read from the evidence on disk (not a slide).

  dataset   experiments/media (CC-licensed photos, videos and audio + rendered panels + synthetic speech) and the
            test-feed cases in demo_data/testkit.json
  runs      experiments/scenarios/<run>/results.json, written by scripts/scenarios.py against the real Agora agent
  lessons   experiments/FAILURES.md: every failure found, its root cause and the fix (each fix has a regression test)
  tests     backend/tests (unit and integration tests that pin each fix)
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .packs import PROJECT_DIR

EXP = PROJECT_DIR / "experiments"


def _runs() -> list[dict[str, Any]]:
    out = []
    for f in sorted((EXP / "scenarios").glob("*/results.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        scen = []
        for name, r in data.items():
            if not isinstance(r, dict):
                continue
            all_steps = [s for s in r.get("steps") or [] if isinstance(s, dict)]
            # A step where nothing reached the agent (no transcript, no reply) is an infrastructure gap, not a model result.
            steps = [s for s in all_steps if s.get("heard") or s.get("replies")]
            checks = [c for s in steps for c in (s.get("checks") or [])]
            ok = sum(1 for c in checks if len(c) > 1 and c[1] is True)
            scen.append({"scenario": name, "steps": len(steps), "unscored_steps": len(all_steps) - len(steps), "checks": len(checks), "passed": ok,
                         "failed_checks": [c[0] for s in steps for c in (s.get("checks") or []) if len(c) > 1 and c[1] is not True][:6],
                         "median_latency_ms": _median([s.get("latency_ms") for s in steps if s.get("latency_ms")])})
        total, passed = sum(s["checks"] for s in scen), sum(s["passed"] for s in scen)
        if not total:
            continue
        run_id = f.parent.name
        try:
            when = datetime.strptime(run_id, "%Y%m%d-%H%M%S").isoformat()
        except ValueError:
            when = None
        out.append({"run": run_id, "when": when, "checks": total, "passed": passed, "pass_rate": round(100 * passed / total, 1), "scenarios": scen})
    return out


def _median(xs: list[float]) -> float | None:
    xs = sorted(x for x in xs if isinstance(x, (int, float)))
    return xs[len(xs) // 2] if xs else None


def _lessons() -> list[dict[str, str]]:
    f = EXP / "FAILURES.md"
    if not f.exists():
        return []
    rows = []
    for line in f.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|(.+?)\|(.+?)\|(.+?)\|\s*$", line)
        if m:
            sym = m.group(2).strip()
            rows.append({"n": m.group(1), "symptom": sym, "cause": m.group(3).strip(), "fix": m.group(4).strip(),
                         "found_live": sym.lower().startswith(("live", "**live")) or "live" in sym.lower()[:20]})
    return rows


def _media() -> dict[str, Any]:
    root = EXP / "media"
    try:
        sources = json.loads((root / "MEDIA_SOURCES.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        sources = []
    gen = sorted(p.name for p in (root / "generated").glob("*") if p.suffix in (".png", ".webm", ".wav", ".jpg"))
    kinds = {"image": 0, "video": 0, "audio": 0}
    for name in [s["file"] for s in sources] + gen:
        ext = Path(name).suffix.lower()
        kinds["image" if ext in (".jpg", ".png") else "video" if ext in (".webm", ".mp4") else "audio"] += 1
    return {"sources": sources, "generated": gen, "kinds": kinds}


def _tests() -> dict[str, Any]:
    tests = []
    for f in sorted((PROJECT_DIR / "backend" / "tests").glob("test_*.py")):
        names = re.findall(r"^def (test_\w+)", f.read_text(encoding="utf-8"), re.M)
        tests.append({"file": f.name, "count": len(names), "names": names})
    return {"files": tests, "total": sum(t["count"] for t in tests)}


def summary() -> dict[str, Any]:
    from . import testkit
    runs = _runs()
    kit = testkit._kit()
    return {"runs": runs, "lessons": _lessons(), "media": _media(), "tests": _tests(),
            "cases": {"scenes": len(kit.get("scenes", [])), "lines": len(kit.get("lines", [])),
                      "scenarios": sorted({s["scenario"] for r in runs for s in r["scenarios"]})}}
