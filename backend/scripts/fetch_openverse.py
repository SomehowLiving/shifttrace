"""Fetch Creative Commons test media via the Openverse API (Flickr images, Freesound CC0 audio).
Test DATA only; attribution recorded in experiments/media/MEDIA_SOURCES.json.

    uv run python scripts/fetch_openverse.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2] / "experiments" / "media"
UA = "shifttrace-test/0.1 (hackathon prototype media test)"
# (endpoint, query, predicate on result, local filename prefix, max items)
WANT = [
    ("images", "industrial control panel", lambda r: r["title"] == "Industrial control panel" and r["width"] >= r["height"], "img_real_panel", 5),
    ("images", "gas compressor", lambda r: r["title"] == "Gas Compressor", "img_real_gas_compressor", 1),
    ("images", "compressor", lambda r: "Westinghouse Compressor, connections" in r["title"], "img_real_westinghouse", 1),
    ("images", "air compressor", lambda r: r["title"].startswith("Folding Truck Bed Cover with VMAC"), "img_real_vmac", 1),
    ("images", "pressure gauge", lambda r: r["license"] in ("by", "by-sa", "cc0", "pdm") and (r.get("width") or 0) >= 640, "img_real_gauge", 1),
    ("audio", "factory machine", lambda r: r["license"] == "cc0" and r["provider"] == "freesound", "aud_real_factory", 2),
]


def get(c: httpx.Client, url: str, **kw) -> httpx.Response:
    last = None
    for attempt in range(8):
        try:
            r = c.get(url, **kw)
        except httpx.HTTPError as e:  # Openverse/Flickr occasionally drop connections
            last = e
            print(f"  {type(e).__name__} on {url[:70]}; retrying", flush=True)
            time.sleep(8 * (attempt + 1))
            continue
        if r.status_code == 200:
            return r
        last = r
        wait = min(int(r.headers.get("retry-after", 0) or 0) or 10 * (attempt + 1), 60)
        print(f"  HTTP {r.status_code} on {url[:70]}; waiting {wait}s", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"giving up on {url}: {last}")


def main() -> None:
    out = ROOT / "web"
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "MEDIA_SOURCES.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    have = {m["file"] for m in manifest}
    with httpx.Client(headers={"User-Agent": UA}, timeout=90, follow_redirects=True) as c:
        for kind, q, pred, prefix, n in WANT:
            res = get(c, f"https://api.openverse.org/v1/{kind}/", params={"q": q, "page_size": 20}).json()["results"]
            picked = [r for r in res if pred(r) and r.get("provider") != "wikimedia"][:n]  # Wikimedia blocks us (HTTP 429)
            if not picked:
                print(f"{prefix}: no match", flush=True)
            for i, r in enumerate(picked):
                ext = ".mp3" if kind == "audio" else ".jpg"
                name = f"{prefix}_{i + 1}{ext}" if n > 1 else f"{prefix}{ext}"
                if name in have and (out / name).exists():
                    continue
                try:
                    data = get(c, r["url"]).content
                except Exception as e:
                    print(f"{name}: skipped ({e})", flush=True)
                    continue
                (out / name).write_bytes(data)
                manifest.append({"file": name, "title": r["title"], "source": r.get("foreign_landing_url"), "creator": r.get("creator"),
                                 "license": f"{r['license']} {r.get('license_version') or ''}".strip(), "provider": r["provider"],
                                 "bytes": len(data), "downloaded": time.strftime("%Y-%m-%d")})
                manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
                print(f"{name}: {len(data) / 1e6:.2f} MB  {r['license']} by {r.get('creator')}", flush=True)
                time.sleep(2)
            time.sleep(4)


if __name__ == "__main__":
    main()
