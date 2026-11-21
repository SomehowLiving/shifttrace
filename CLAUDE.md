# SHIFTTRACE: agent instructions and invariants

Hackathon project for PS31 (Build with Agora, Bengaluru, 21 Nov 2026). Background: `docs/01..03_*.md`. Current truth: `PROJECT_STATUS.md`.

## Invariants (do not break)
- Voice path is Agora ConvoAI + **Murf FALCON TTS**. Never substitute browser speechSynthesis or another TTS. Do not switch to Agora MLLM mode: it disables the TTS module, which removes Murf.
- The LLM can never approve its own action. `approve_procurement_request` only succeeds on (a) the technician's final transcript after the agent's read-back (`transcript_events` ordering) or (b) a console click.
- Every mutation is re-read on a fresh connection before reporting `verified`. Never report success without it.
- Evidence always carries `source_type`; model output is `camera_model` / `agent_inference`, never presented as a confirmed diagnosis.
- Only the MCP port is tunnelled. It requires `Authorization: Bearer $MCP_TOKEN`. The console API binds to 127.0.0.1. Hosted mode (`SHIFTTRACE_SINGLE_PORT=1`, Dockerfile/render.yaml) serves both on $PORT and refuses to start without `CONSOLE_PASSWORD`.
- Secrets live only in `backend/.env`. Never print them; `agent_config_json` is stored redacted.
- Demo data is synthetic. Do not add real people, plants, or brands.
- Use cases are configuration: machines/history in `demo_data/packs/<id>/pack.json`, session tasks in `demo_data/tasks.json` (guide: `docs/CONFIGURING_USE_CASES.md`). Do not hard-code an asset ID, manual section or safety rule in backend code; put it in a pack. A task's `tools` allowlist is enforced in both Agora `allowed_tools` and `tools._check_task_allows`. Tasks without `tools` get `CORE_TOOLS`; domain tools (warehouse, training) are opt-in.
- Every consequential action is drafted, read back and confirmed by the worker's own words (procurement and stock transfers share `find_spoken_approval`). Training answers are marked in code against pack key points, never by the LLM.

## Commands (Windows: uv's .exe shims are blocked by Application Control; always use `python -m`)
- Backend: `cd backend; uv run python -m app.main`
- Tests: `cd backend; uv run python -m pytest -q`
- Preflight: `cd backend; uv run python -m app.preflight`
- UI smoke: `cd backend; uv run python scripts/ui_smoke.py [--voice]`
- Frontend: `cd frontend; npx tsc -b; npx vite build` (dev server: `npx vite`, proxies /api to :8000)
- Reset data: `cd backend; uv run python -m app.seed` or POST /api/demo/reset

## Layout
- `backend/app/services.py` domain logic · `tools.py` tool runner (audit, verify, SSE) · `mcp_server.py` Agora-facing tools
- `backend/app/packs.py` pack + task loading · `seed.py` loads selected packs (`SHIFTTRACE_PACKS`)
- `backend/app/agora_session.py` agent config and lifecycle (prompt = generic rules + task section + machine safety notes) · `api.py` console REST + SSE · `tunnel.py` cloudflared
- `frontend/src/voice.ts` Agora RTC/RTM/toolkit · `pages/LiveSession.tsx` main screen
