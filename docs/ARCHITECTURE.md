# Architecture

## Components

| Component | Tech | Responsibility |
|---|---|---|
| Technician console | React 19, Vite, Tailwind 4, `agora-rtc-sdk-ng` 4.24, `agora-rtm` 2.3, `agora-agent-client-toolkit` 2.9 | Publishes mic + camera to Agora RTC; plays agent audio; receives transcripts and agent state over RTM; relays transcripts and JPEG snapshots to the backend; shows evidence, tool calls, approvals, handoffs |
| Agora ConvoAI agent | `agora-agents` 2.15 Python SDK → `POST /api/conversational-ai-agent/v2/projects/{appid}/join` | ASR Deepgram nova-3 (managed), LLM gpt-4o-mini (managed, `input_modalities: [text, image]`), TTS Murf FALCON (BYOK), MCP tools, RTM data channel |
| MCP server | `mcp` 1.30 FastMCP, streamable HTTP, port 8001 | 21 tools Agora cloud calls: 16 core (incl. `record_reading`, a deterministic limit check, and `schedule_follow_up`) and 6 opt-in domain tools (warehouse: `track_shipment`, `create_stock_transfer`, `confirm_stock_transfer`; training: `get_training_module`, `record_training_answer`, `finish_training_module`). Bearer-token guard; `X-Shifttrace-Session` header binds calls to a maintenance session |
| Console API | FastAPI, port 8000 (127.0.0.1) | REST for the console, SSE stream, console approvals, demo controls, static console |
| Tunnel | Cloudflare quick tunnel (`cloudflared`) started by the backend | Public HTTPS URL for the MCP port only; self-tested with an MCP `initialize` through the public URL |
| Store | SQLite (WAL) | assets, work orders + log, sessions, evidence, parts, reservations, procurement, escalations, tool_actions, transcripts, transcript_events, handoffs, manual chunks |

## One voice turn with a tool call
1. Technician speaks; RTC carries audio to Agora; Deepgram transcribes.
2. The managed LLM sees the conversation plus recent camera frames (Agora forwards frames from the published video track when `input_modalities` includes `image`; per the official Vision Recipe; see verification status).
3. The LLM calls an MCP tool; Agora POSTs to `https://<tunnel>/mcp` with our bearer token and session header.
4. `tools.run_tool` runs the tool in a transaction, re-reads mutated rows on a fresh connection (`verified`), writes `tool_actions`, publishes an SSE event.
5. Agora feeds the result to the LLM; the reply is synthesised by Murf FALCON and played over RTC.
6. The console receives the transcript via RTM and POSTs it to `/api/sessions/{id}/transcripts` (display copy + append-only `transcript_events`).

## Approval gate (procurement)
- `create_procurement_request` stores `PENDING_APPROVAL` and a `transcript_watermark` (last transcript event id).
- `approve_procurement_request` succeeds only if, after the watermark, an **agent** transcript event exists (the read-back) and the technician's latest **final** utterance after that is affirmative (and not negated). It waits up to `APPROVAL_WAIT_S` (4 s) for the relayed transcript.
- Alternatively, the console Approve button submits directly, then `think` injects the verified result into the live agent.
- Duplicate drafts/approvals are idempotent (`dedupe_key` = part + work order).

## Provenance model
`evidence.source_type`: `camera_model` (model reading of a frame), `technician`, `cmms` (system record), `tool_result` (system write), `agent_inference` (hypothesis/open question). Hypotheses and open questions have `status` open → confirmed / ruled_out / answered, closed with `update_open_item`, which writes a linked technician statement.

## Handoff
`services.compose_handoff` is deterministic: it reads only persisted evidence, tool actions, procurement, reservations, work-order log, escalations and open loops. The agent speaks a short version of `spoken_summary`. No LLM writes the stored handoff.

## Security boundaries
- Only port 8001 is public, and it requires the bearer token. FastMCP's DNS-rebinding guard is disabled explicitly because tunnel Host headers are not localhost; the token is the control.
- Console API binds to 127.0.0.1; CORS only for the Vite dev origin.
- Murf key and agent token never reach the browser. The browser gets a short-lived RTC+RTM client token.

## Configuration layer: packs and tasks (added 21 Nov)
- `backend/app/packs.py` loads `demo_data/packs/<id>/pack.json` (machines, manuals, parts, work orders, sessions, evidence, handoffs; relative `ago:` timestamps) and `demo_data/tasks.json`.
- `seed.py` seeds the packs selected by `SHIFTTRACE_PACKS`. Each asset records its pack in `metadata.pack`.
- At session start the console sends `task_id`. `api.start_session` checks it against the asset's `metadata.tasks` and stores it on `sessions.task_id`.
- `agora_session.build_instructions(asset, technician, shift, task)` = generic grounding, approval and camera rules + the task's goal and procedure + the machine's `safety_notes`. The greeting comes from the task, and `allowed_tools` from the task's `tools`.
- `tools.run_tool` → `_check_task_allows` rejects agent calls outside the task's allowlist (`not_available_in_task`). Console calls are not restricted.
- `compose_handoff` writes `task` into the report and takes its safety step from the machine.
- Guide: `docs/CONFIGURING_USE_CASES.md`.
