# Agora integration

Sources (fetched 19 Nov 2026 via `https://docs.agora.io/en/llms.txt` → "Conversational AI — Main"):
- Join API: https://docs.agora.io/en/api-reference/api-ref/conversational-ai/join
- Token auth: https://docs.agora.io/en/api-reference/api-ref/conversational-ai/authentication
- Managed mode: https://docs.agora.io/en/ai/build/managed-mode
- MCP tools: https://docs.agora.io/en/ai/build/tools/mcp-tools
- Send images: https://docs.agora.io/en/ai/build/send-multimodal-messages
- Reference code: AgoraIO-Conversational-AI/recipe-agent-vision @ 01cf543 (2026-08-17), recipe-agent-rpg @ f0ef334 (2026-08-25), MIT. Patterns read, no code copied verbatim.

## API version choice
Agora publishes two doc sets: **Main** (`/v2/projects/{appid}/join`, inline provider config) and **Preview** (`/conversational-ai/v1/projects/{appid}/agents|sessions`, saved agents and secret sets). We use **Main**: it is what the official recipes and the `agora-agents` 2.15 SDK `create_async_session().start()` use, and Murf works with an inline key there.

## Agent configuration (as sent; secrets redacted, stored per session in `sessions.agent_config_json`)
- `asr`: `deepgram`, `en`; managed via SDK-inferred preset `deepgram_nova_3`
- `llm`: OpenAI `gpt-4o-mini`, managed via preset `openai_gpt_4o_mini` (no key), `input_modalities: ["text","image"]`, system prompt in `agora_session.build_instructions`, `max_history: 40`, `mcp_servers: [{name: shifttrace, endpoint: <tunnel>/mcp, transport: streamable_http, headers: {Authorization, X-Shifttrace-Session}, allowed_tools: [14 names], timeout_ms: 10000}]`
- `tts`: `murf`, `params: {api_key, base_url: wss://global.api.murf.ai/v1/speech/stream-input, voiceId, locale, model: FALCON, sample_rate: 24000}`
- `advanced_features: {enable_rtm: true, enable_tools: true}`, `parameters: {data_channel: rtm, enable_error_message, enable_metrics, audio_scenario: chorus}`
- `turn_detection`: VAD, 640 ms end-of-speech silence; `idle_timeout: 120`
- REST auth: `Authorization: agora token="<ConvoAI+RTC+RTM token>"` generated from App ID + Certificate (no customer ID/secret needed).

## Agora features used
| Feature | Where | Status |
|---|---|---|
| ConvoAI join/leave | `agora_session.start/stop` | implemented-not-tested (needs keys) |
| Managed ASR + LLM | agent config | implemented-not-tested |
| Camera frames to LLM (`input_modalities` image) | agent config + published camera track | implemented-not-tested; must be verified with a real panel read |
| MCP tools over streamable HTTP | `mcp_server.py` | verified-local (MCP client over HTTP, tunnel `initialize` PASS); Agora→MCP call not yet observed |
| RTM transcripts + agent state | `voice.ts` via toolkit | implemented-not-tested |
| `think` (inject console approval result) | `api.approve_from_console` | implemented-not-tested |
| Typed messages (`sendText`) | live session text box | implemented-not-tested |

## Gotchas found
- FastMCP 1.30 enables DNS-rebinding protection by default when bound to 127.0.0.1 and would reject tunnel Host headers. Disabled explicitly; bearer token enforced instead. Covered by `test_accepts_tunnel_host_header`.
- `allowed_tools` names must exactly match registered tool names, or Agora may hang mid-response (Agora docs warning). `TOOL_NAMES` is asserted against `tools/list` in tests.
- Agora counts at most 32 tools; we expose 14.
- `agora-rtm` 2.3 emits `linkState` (the recipe's older RTM used `status`).
- MLLM mode (e.g. Gemini Live via Agora) "automatically disables ASR, LLM, and TTS", which would remove Murf. Not used.
