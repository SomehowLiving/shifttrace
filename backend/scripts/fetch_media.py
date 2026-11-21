"""Fetch the freely licensed Wikimedia Commons test media listed in experiments/media_candidates.json.

Files are test DATA only (camera/noise inputs), saved under experiments/media/web/ with an attribution
manifest. Polite pacing: one request at a time, honours Retry-After on HTTP 429.

    uv run python scripts/fetch_media.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2] / "experiments"
UA = "shifttrace-test/0.1 (hackathon prototype media test)"
NAMES = {
    "60163": "vid_tornado_compressor.ogv", "machinekamer": "aud_ship_engine_room.ogg", "Apollo": "img_annunciator_panel.jpg",
    "gas blending": "img_gas_blending_panel.jpg", "Compressor motor": "aud_compressor_motor.ogg",
    "machinery operation": "img_machinery_control_panel.jpg", "pressure gauge": "img_pressure_gauge.jpg",
    "Kaeser": "img_screw_compressor_unit_a.jpg", "Rotary-screw": "img_screw_compressor_unit_b.jpg",
    "Ultrasound": "vid_reciprocating_compressor.webm", "WWS Compressor": "aud_workshop_compressor.ogg",
}


def main() -> None:
    out = ROOT / "media" / "web"
    out.mkdir(parents=True, exist_ok=True)
    items = json.loads((ROOT / "media_candidates.json").read_text(encoding="utf-8"))
    manifest_path = ROOT / "media" / "MEDIA_SOURCES.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    done = {m["file"] for m in manifest}
    with httpx.Client(headers={"User-Agent": UA}, timeout=120, follow_redirects=True) as c:
        for it in items:
            local = next(v for k, v in NAMES.items() if k in it["title"])
            if local in done and (out / local).exists():
                continue
            url = it["thumb"] or it["url"]
            for attempt in range(8):
                r = c.get(url)
                if r.status_code == 200:
                    break
                wait = int(r.headers.get("retry-after", 0) or 0) or 30 * (attempt + 1)
                print(f"{local}: HTTP {r.status_code}, waiting {wait}s", flush=True)
                time.sleep(wait)
            else:
                print(f"{local}: GAVE UP", flush=True)
                continue
            (out / local).write_bytes(r.content)
            manifest.append({"file": local, "source": it["page"], "license": it["license"], "author": it["artist"],
                             "bytes": len(r.content), "downloaded": time.strftime("%Y-%m-%d")})
            manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
            print(f"{local}: {len(r.content) / 1e6:.2f} MB", flush=True)
            time.sleep(8)
    print("DONE", len(manifest), "files", flush=True)


if __name__ == "__main__":
    main()
