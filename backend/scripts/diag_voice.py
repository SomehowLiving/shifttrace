"""One short live session for debugging the voice link: joins, waits for the greeting, speaks one line,
then dumps the in-page event log (RTC/RTM states, raw RTM/stream messages) and filtered console.

    uv run python scripts/diag_voice.py [utterance_key]
"""
import json
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
import scenarios as S  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

key = sys.argv[1] if len(sys.argv) > 1 else "bearing_stock"
out = S.ROOT / "experiments" / "scenarios" / "diag"
out.mkdir(parents=True, exist_ok=True)
S.api.post("/api/demo/reset")
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True, args=["--use-fake-ui-for-media-stream", "--autoplay-policy=no-user-gesture-required"])
    s = S.Session(b, "diag", "Kavya Rao", "A shift", out)
    msgs: list[str] = []
    s.page.on("console", lambda m: msgs.append(f"{m.type}: {m.text[:300]}"))
    try:
        s.page.wait_for_timeout(16000)
        s.page.evaluate("(u) => window.__fake.say(u)", S.media_url(f"utt_{key}.wav"))
        s.page.wait_for_timeout(18000)
        log = s.page.evaluate("() => window.__shifttrace.log.map(e => [e.t, e.kind, JSON.stringify(e.data).slice(0, 220)])")
        t0 = log[0][0] if log else 0
        for t, k, d in log:
            print(f"+{(t - t0) / 1000:6.1f}s {k:14} {d}")
        print("--- transcript_events:", json.dumps(S.api.get(f"/api/sessions/{s.sid}/transcript-events").json())[:800])
        print("--- tool calls:", [(t["tool_name"], t["status"]) for t in S.api.get(f"/api/tool-actions?session_id={s.sid}").json()])
        print("--- console")
        for m in msgs:
            if any(k in m.lower() for k in ("error", "rtm", "transcri", "agentvoice", "toolkit", "fail")):
                print(m[:260])
    finally:
        print("close:", {k: v for k, v in s.close().items() if k != "agent_config_tts"})
    b.close()
