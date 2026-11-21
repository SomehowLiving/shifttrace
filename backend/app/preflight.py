"""Credential and integration preflight. Never prints secret values; never starts a billable agent.

    uv run python -m app.preflight
"""
from __future__ import annotations

import random
import sys

import httpx
from agora_agent.agentkit.token import generate_convo_ai_token

from .config import settings


def line(status: str, name: str, detail: str = "") -> None:
    print(f"[{status:>4}] {name}{': ' + detail if detail else ''}")


def check_murf() -> bool:
    if not settings.murf_ready:
        line("FAIL", "MURF_API_KEY", "missing in backend/.env")
        return False
    try:
        r = httpx.get("https://api.murf.ai/v1/speech/voices", params={"model": "falcon-2.1"},
                      headers={"api-key": settings.murf_api_key}, timeout=15)
    except httpx.HTTPError as e:
        line("FAIL", "Murf voices API", f"{type(e).__name__}")
        return False
    if r.status_code != 200:
        line("FAIL", "Murf voices API", f"HTTP {r.status_code} (key rejected or no API access)")
        return False
    voices = r.json()
    ids = {v.get("voiceId") for v in voices}
    line("OK", "Murf key accepted", f"{len(voices)} Falcon 2.1 voices available")
    if settings.murf_voice_id in ids:
        v = next(v for v in voices if v.get("voiceId") == settings.murf_voice_id)
        line("OK", "MURF_VOICE_ID", f"{settings.murf_voice_id} ({v.get('gender')}, {v.get('locale')})")
    else:
        line("FAIL", "MURF_VOICE_ID", f"'{settings.murf_voice_id}' is not a Falcon voice on this account")
    for loc in ("en-US", "en-IN", "en-UK", "en-GB"):
        sample = [f"{v['voiceId']}({v.get('gender', '?')[0]})" for v in voices if v.get("locale") == loc][:10]
        if sample:
            print(f"        {loc}: {', '.join(sample)}")
    return settings.murf_voice_id in ids


def check_agora() -> bool:
    if not settings.agora_ready:
        line("FAIL", "AGORA_APP_ID / AGORA_APP_CERTIFICATE", "missing in backend/.env")
        return False
    token = generate_convo_ai_token(settings.agora_app_id, settings.agora_app_certificate,
                                    channel_name=f"preflight-{random.randint(1000, 9999)}", uid=0, token_expire=600)
    url = f"https://api.agora.io/api/conversational-ai-agent/v2/projects/{settings.agora_app_id}/agents"
    try:
        r = httpx.get(url, params={"limit": 5}, headers={"Authorization": f'agora token="{token}"'}, timeout=15)
    except httpx.HTTPError as e:
        line("FAIL", "Agora ConvoAI REST", type(e).__name__)
        return False
    if r.status_code == 200:
        line("OK", "Agora ConvoAI REST", "credentials accepted, Conversational AI reachable")
        return True
    line("FAIL", "Agora ConvoAI REST", f"HTTP {r.status_code}: {r.text[:200]}")
    return False


def check_tunnel() -> bool:
    try:
        r = httpx.get(f"http://127.0.0.1:{settings.api_port}/api/health", timeout=5)
        t = r.json().get("tunnel", {})
    except Exception:
        line("SKIP", "Tunnel", "backend not running (start it with: uv run python -m app.main)")
        return False
    ok = bool(t.get("self_test"))
    line("OK" if ok else "FAIL", "MCP tunnel", f"{t.get('url')} self-test={t.get('self_test')} {t.get('error') or ''}")
    return ok


if __name__ == "__main__":
    results = [check_agora(), check_murf(), check_tunnel()]
    sys.exit(0 if all(results) else 1)
