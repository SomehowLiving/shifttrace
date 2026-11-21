# Decision log

| Date | Decision | Alternatives | Reason |
|---|---|---|---|
| 19 Nov | Concept: SHIFTTRACE + open-loop ledger (see `research/PRODUCT_IDEATION.md`) | Camera-verified procedures; talk-to-the-machine | Covers all PS31 stages; "what is still unknown" is the distinctive, demoable insight; avoids safety claims |
| 19 Nov | No local multimodal model | MiniCPM-o 4.5, Realtime-Venus | No CUDA GPU; their native speech would not satisfy Murf anyway |
| 19 Nov | Agora Main `/join` API via `agora-agents` SDK | Preview agents/sessions API | Used by the official recipes; inline Murf key; fewer moving parts |
| 19 Nov | Managed ASR + managed vision LLM | Custom LLM endpoint with our own key | Only 3 secrets needed; no extra hop; Agora remains the brain of the conversation |
| 19 Nov | Tools via MCP (`streamable_http`), not custom HTTP tools | `llm.tools` custom tools | One server, typed schemas, `tools/list` testable; recipe-proven with Agora |
| 19 Nov | Separate MCP port, tunnelled alone, bearer token + session header | Tunnel the whole API (recipe default) | Smallest public surface; per-session binding |
| 19 Nov | Server-side approval gate from relayed transcripts | Trust the LLM's tool call; UI-only approval | Hands-free approval that the LLM cannot fake; console fallback |
| 19 Nov | Deterministic handoff composer | LLM-written handoff | Every line traceable to a record; zero invented facts |
| 19 Nov | BM25 over manual sections | Embeddings + vector DB | Tiny corpus; deterministic; no key |
| 19 Nov | Auto-start Cloudflare quick tunnel + self-test | Manual ngrok step | One command; failure is visible at startup |
| 19 Nov | Vite + React + Tailwind console served by FastAPI | Next.js (recipes) | Single process to run; static build |
| 19 Nov | Claim guard outside the model | Prompt-only grounding | Prompt rules were ignored when tools vanished (observed); enforcement must not depend on the model |
| 19 Nov | Verify Agora↔tools link per session, retry or refuse | Trust the start API | ~1/3 starts had no tools; an agent without tools is worse than no agent |
| 19 Nov | Openverse (Flickr/Freesound) for real-world test media | Wikimedia Commons | Commons returned 429 to every download; Openverse items are CC-licensed with attribution metadata |
| 21 Nov | Use cases as data: packs (machines/history/manuals/panel) + tasks (goal/procedure/tools) | Hard-coded C-204 seed and prompt; LLM-generated scenarios | Same engine for any machine or job; packs stay synthetic and reviewable; tasks can narrow tools, which is a safety control, not just a prompt hint |
| 21 Nov | Per-task tool allowlist enforced server-side as well as in Agora `allowed_tools` | Prompt instruction only | Prompt-only restrictions were ignored before (claim guard history); a briefing session must not be able to write |
