"""The Agora request is built offline exactly as the SDK's start() would, then checked."""
import json

from app.agora_session import agora_sessions
from app.config import settings
from app.db import connect
from app.mcp_server import CORE_TOOLS, TOOL_NAMES
from app import services as svc


def test_agent_request_uses_murf_falcon_vision_and_mcp(monkeypatch):
    monkeypatch.setattr(settings, "agora_app_id", "0123456789abcdef0123456789abcdef")
    monkeypatch.setattr(settings, "agora_app_certificate", "fedcba9876543210fedcba9876543210")
    monkeypatch.setattr(settings, "murf_api_key", "murf-secret-value")
    monkeypatch.setattr(settings, "mcp_public_url", "https://example.trycloudflare.com")
    monkeypatch.setattr(settings, "mcp_token", "mcp-secret-value")
    conn = connect()
    asset = svc.get_asset(conn, "C-204")
    conn.close()
    agent = agora_sessions.build_agent("S-1001", asset, "Kavya Rao", "A shift")
    session = agent.create_async_session(channel="st-test", agent_uid="12345678", remote_uids=["4321"],
                                         idle_timeout=120, enable_string_uid=False, expires_in=3600)
    preview = agora_sessions.request_preview(session)
    assert "error" not in preview, preview
    p = agora_sessions.redacted_properties(preview)

    assert p["tts"]["vendor"] == "murf"
    assert p["tts"]["params"]["model"] == "FALCON"
    assert p["tts"]["params"]["base_url"] == "wss://global.api.murf.ai/v1/speech/stream-input"
    assert p["llm"]["input_modalities"] == ["text", "image"]
    assert "openai_gpt_4o_mini" in p["_preset"] and "deepgram_nova_3" in p["_preset"]
    assert p["advanced_features"] == {"enable_rtm": True, "enable_tools": True}
    fw = p["filler_words"]
    assert fw["enable"] is True and fw["trigger"]["fixed_time_config"]["response_wait_ms"] == 1200
    assert fw["content"]["mode"] == "static" and len(fw["content"]["static_config"]["phrases"]) >= 3
    mcp = p["llm"]["mcp_servers"][0]
    assert mcp["endpoint"] == "https://example.trycloudflare.com/mcp" and mcp["transport"] == "streamable_http"
    assert mcp["headers"]["X-Shifttrace-Session"] == "S-1001"
    assert sorted(mcp["allowed_tools"]) == sorted(CORE_TOOLS)  # domain tools (warehouse, training) are opt-in per task
    dumped = json.dumps(p)
    for secret in ("murf-secret-value", "mcp-secret-value", "fedcba9876543210fedcba9876543210"):
        assert secret not in dumped
