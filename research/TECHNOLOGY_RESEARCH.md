# Technology research log (19 Nov 2026)

| Item | What was checked | Finding | Label |
|---|---|---|---|
| Agora docs | `llms.txt` indexes; Main and Preview ConvoAI guides; join, auth, managed mode, MCP, send-images, Murf pages (raw markdown) | Two API generations. Main supports managed ASR/LLM, inline Murf key, MCP `streamable_http`, `input_modalities` image | verified (docs) |
| recipe-agent-vision @01cf543 | `server/src/agent.py`, `vision_config.py`, web toolkit wiring | Managed gpt-4o-mini + `input_modalities [text,image]`; "Agora captures the user's published camera track and forwards frames as image content to the LLM" | code-reference-only |
| recipe-agent-rpg @f0ef334 | `mcp_server.py`, `mcp_config.py`, README | FastMCP mounted in-process; public tunnel required; `streamable_http` (Agora) vs `streamable-http` (FastMCP) naming | code-reference-only |
| agora-agents 2.15 (PyPI) | `vendors/llm.py`, `vendors/tts.py`, `agent_session.py`, `token.py` | Managed models: gpt-4o-mini, gpt-4.1-mini, gpt-5-nano, gpt-5-mini; MurfTTS → `params.api_key/base_url/voiceId/model`; `say`, `think`, `interrupt` | verified (source) |
| mcp 1.30 | FastMCP settings, transport security | DNS-rebinding guard defaults on for 127.0.0.1 → must disable behind a tunnel | verified-local (test) |
| Murf docs | stream-input reference, voices API | FALCON → Falcon 2.1; voice list API; bad key closes WS with 1008 | verified (docs) |
| cloudflared 2026.11.1 | quick tunnel to :8001 | MCP `initialize` through the public URL: PASS | verified-local |
| MiniCPM-o 4.5, Realtime-Venus | hardware fit | No CUDA GPU → not runnable | blocked |
| Gemini Live via Agora | Agora MLLM docs | MLLM mode disables the TTS module (Murf) | not-supported for our requirement |

Corrections to the earlier brief:
- "Murf requires a secret set" applies to the Preview API only.
- The send-images guide URL is `/en/ai/build/send-multimodal-messages`; it describes RTM image messages with a public image URL. Camera-track frame forwarding is a separate path, shown in the Vision Recipe.
- "Use Murf through Agora" holds; the Murf model value `FALCON` resolves to Falcon 2.1.
