"""Grow the test-media dataset from Creative Commons sources (Openverse: Flickr images, Freesound audio), then build
short "hand-held camera" videos from the photos with ffmpeg. Test DATA only. Every file's title, creator, licence and
source URL is recorded in experiments/media/MEDIA_SOURCES.json, with a label saying what the camera should see.

    uv run python scripts/fetch_dataset.py            # fetch what is missing, then build videos
    uv run python scripts/fetch_dataset.py --videos   # only (re)build videos from what is already downloaded

Downloads are treated as untrusted data: only image/jpeg, image/png and audio/mpeg responses under 8 MB are kept.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2] / "experiments" / "media"
WEB, GEN = ROOT / "web", ROOT / "generated"
UA = "shifttrace-test/0.2 (hackathon prototype; test media dataset)"
OK_LICENSES = {"cc0", "pdm", "by", "by-sa"}
OK_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "audio/mpeg": ".mp3"}
MAX_BYTES = 8 * 1024 * 1024

# (kind, query, filename prefix, how many, label: what a vision model should be able to say about it)
WANT = [
    ("images", "industrial control panel alarm", "img_ds_panel", 3, "industrial control panel with indicators; codes may not be legible"),
    ("images", "pressure gauge industrial", "img_ds_gauge", 3, "analogue pressure gauge; needle reading may be estimated, not exact"),
    ("images", "conveyor belt factory", "img_ds_conveyor", 3, "belt conveyor in a factory"),
    ("images", "warehouse shelves pallets", "img_ds_warehouse", 3, "warehouse racking with pallets or cartons"),
    ("images", "forklift warehouse", "img_ds_forklift", 2, "forklift in a warehouse aisle; a pedestrian safety context"),
    ("images", "air handling unit hvac", "img_ds_hvac", 2, "HVAC air handling equipment or ductwork"),
    ("images", "electric motor industrial", "img_ds_motor", 2, "industrial electric motor"),
    ("images", "industrial air compressor", "img_ds_compressor", 2, "industrial air compressor"),
    ("images", "digital temperature display", "img_ds_display", 2, "digital display showing a number"),
    ("audio", "forklift beeping", "aud_ds_forklift", 1, "forklift reversing alarm (background noise)"),
    ("audio", "conveyor belt noise", "aud_ds_conveyor", 1, "conveyor running (background noise)"),
]
VIDEOS = [  # (output, source prefix, label)
    ("vid_ds_conveyor_pan.webm", "img_ds_conveyor", "hand-held pan along a factory conveyor"),
    ("vid_ds_warehouse_pan.webm", "img_ds_warehouse", "hand-held walk past warehouse racking"),
    ("vid_ds_gauge_zoom.webm", "img_ds_gauge", "hand-held zoom onto pressure gauges, slight shake"),
]


def get(c: httpx.Client, url: str, **kw) -> httpx.Response | None:
    for attempt in range(6):
        try:
            r = c.get(url, **kw)
        except httpx.HTTPError as e:
            print(f"  {type(e).__name__}; retrying", flush=True)
            time.sleep(6 * (attempt + 1))
            continue
        if r.status_code == 200:
            return r
        if r.status_code in (401, 403, 404):  # anonymous Openverse allows page_size <= 20; a client error will not fix itself
            print(f"  HTTP {r.status_code}; skipping", flush=True)
            return None
        wait = min(int(r.headers.get("retry-after", 0) or 0) or 8 * (attempt + 1), 60)
        print(f"  HTTP {r.status_code}; waiting {wait}s", flush=True)
        time.sleep(wait)
    return None


def fetch() -> None:
    WEB.mkdir(parents=True, exist_ok=True)
    mpath = ROOT / "MEDIA_SOURCES.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else []
    have = {m["file"] for m in manifest}
    with httpx.Client(headers={"User-Agent": UA}, timeout=60, follow_redirects=True) as c:
        for kind, q, prefix, n, label in WANT:
            if sum(1 for f in have if f.startswith(prefix)) >= n:
                continue
            r = get(c, f"https://api.openverse.org/v1/{kind}/", params={"q": q, "page_size": 20, "license": ",".join(sorted(OK_LICENSES))})
            if r is None:
                print(f"{prefix}: search failed", flush=True)
                continue
            results = [x for x in r.json().get("results", []) if x.get("license") in OK_LICENSES and x.get("provider") != "wikimedia"
                       and (kind == "audio" or ((x.get("width") or 0) >= 800 and (x.get("width") or 0) >= (x.get("height") or 1)))]
            got = 0
            for x in results:
                if got >= n:
                    break
                f = get(c, x["url"])
                ctype = (f.headers.get("content-type", "").split(";")[0].strip() if f else "")
                if not f or ctype not in OK_TYPES or len(f.content) > MAX_BYTES or len(f.content) < 20_000:
                    continue
                name = f"{prefix}_{got + 1}{OK_TYPES[ctype]}"
                (WEB / name).write_bytes(f.content)
                manifest.append({"file": name, "title": x.get("title"), "source": x.get("foreign_landing_url") or x.get("url"),
                                 "creator": x.get("creator"), "license": f"{x.get('license')} {x.get('license_version') or ''}".strip(),
                                 "provider": x.get("provider"), "bytes": len(f.content), "downloaded": time.strftime("%Y-%m-%d"),
                                 "label": label, "query": q})
                have.add(name)
                got += 1
                print(f"  {name}  {x.get('license')}  {x.get('title')!r}", flush=True)
                time.sleep(1.5)
            mpath.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
            time.sleep(2)


def videos() -> None:
    GEN.mkdir(parents=True, exist_ok=True)
    mpath = ROOT / "MEDIA_SOURCES.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else []
    for out, prefix, label in VIDEOS:
        srcs = sorted(WEB.glob(f"{prefix}_*.jpg"))[:3]
        if not srcs:
            print(f"{out}: no source photos", flush=True)
            continue
        inputs, filters = [], []
        for i, ph in enumerate(srcs):
            inputs += ["-loop", "1", "-t", "5", "-i", str(ph)]
            shake = "+4*sin(on/3)" if "zoom" in out else ""
            filters.append(f"[{i}:v]scale=1600:-2,zoompan=z='min(zoom+0.0015,1.3)':x='iw/2-(iw/zoom/2)+on*0.8{shake}':y='ih/2-(ih/zoom/2){shake}'"
                           f":d=1:s=1280x720:fps=15,trim=duration=5,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v{i}]")  # concat needs matching SAR/format
        concat = "".join(f"[v{i}]" for i in range(len(srcs))) + f"concat=n={len(srcs)}:v=1:a=0[out]"
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters) + ";" + concat,
                            "-map", "[out]", "-c:v", "libvpx", "-b:v", "1500k", str(GEN / out)], check=False)
        if r.returncode == 0:
            manifest = [m for m in manifest if m["file"] != out]
            manifest.append({"file": out, "title": label, "source": "derived (ffmpeg pan/zoom) from " + ", ".join(p.name for p in srcs),
                             "license": "same as source photos", "provider": "derived", "label": label})
            print(f"  {out}", flush=True)
    mpath.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if "--videos" not in sys.argv:
        fetch()
    videos()
