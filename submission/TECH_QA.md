# Shifttrace: technical answers for judges

Every answer below is taken from the code, with the file to point at if a judge wants to see it.

---

## 1. Architecture and the voice pipeline

**Walk me through one voice turn.**
1. **Browser in.** The browser publishes the mic and camera to an Agora RTC channel (`agora-rtc-sdk-ng`).
2. **Agent pipeline.** Our backend starts an Agora Conversational AI agent in that channel through the Agora agent SDK (`agora_session.py`). Its pipeline is:
   - STT: `DeepgramSTT(model="nova-3")`, Agora-managed;
   - LLM: `OpenAI(model="gpt-4o-mini", input_modalities=["text","image"])`, Agora-managed;
   - TTS: `MurfTTS(model="FALCON", sample_rate=24000)`, our own Murf key.
3. **Turn detection.** Server-side VAD: speech threshold 0.5, barge-in after 200 ms of user speech, end of turn after 640 ms of silence.
4. **Tool calls.** When the LLM calls a tool, Agora's cloud calls our MCP server over **streamable HTTP**. Each call carries `Authorization: Bearer <MCP_TOKEN>` and `X-Shifttrace-Session`, which binds the call to the right session.
5. **Answer.** The tool result goes back to the LLM, and the LLM's text is spoken by Murf Falcon over RTC.
6. **Transcripts.** Agora's RTM data channel (`advanced_features.enable_rtm`, `data_channel: "rtm"`) streams transcripts and agent state to the browser through the Agora Voice AI toolkit. The browser relays final transcripts to `/api/sessions/{id}/transcripts`, which feed the approval gate and the claim guard.

**Why MCP and not plain function calling?**
- Agora's LLM module speaks MCP natively (`mcp_servers` in the LLM config). The same tool server can serve any MCP client, such as Claude or IDE agents.
- The tool surface is an explicit, versioned contract (FastMCP, `mcp_server.py`) with an allowlist per session (`allowed_tools`).
- Our code stays the system of record. The LLM never touches the database; it can only call tools.

**How does Agora reach a server on a laptop?**
- **Locally:** only the MCP port (8001) is exposed, through an ngrok static domain. The console API binds to 127.0.0.1.
- **Health check:** `tunnel.py` sends a real MCP `initialize` through the public URL, exactly as Agora would. It tolerates 5 failed probes before restarting the tunnel. If the URL changes mid-call, every live agent is told by an injected system message (`agent.think`) to stop claiming lookups.
- **On Render:** one container serves the console and `/mcp` on `$PORT` (an ASGI dispatcher in `main.py`). The public URL comes from `RENDER_EXTERNAL_URL`, and the console requires HTTP Basic auth.

**How does the model see the camera?**
- The LLM runs with `input_modalities=["text","image"]`, and Agora samples the published camera track and forwards frames to it.
- Separately, the browser uploads a JPEG every 4 s (`/snapshot`), so each visual observation in the timeline carries the exact frame it was based on.
- Live runs showed the agent often *described* the view without calling `record_observation`. `capture.py` therefore records the description deterministically, when the worker's last utterance was about the camera and the agent's reply describes it. These records are labelled `camera_model`, captured from speech, unverified.

**Where is the RAG?**
- Retrieval goes through tools, not a vector store.
- `search_maintenance_manual` runs BM25 (k1 = 1.4, b = 0.75, `services.search_manual`) over the machine's manual sections, which are loaded from its pack. It returns the top 3 with section numbers, and the agent is told to cite them.
- Context also comes from structured retrieval: `get_asset_history`, `get_previous_handoff`, `get_open_items`, `check_inventory`.
- **Why lexical:** manuals are short, and section-level citations must be exact. BM25 is deterministic and testable, and every answer stays traceable to a stored row. A vector index can sit behind the same tool later without changing the agent.

---

## 2. Safety: why the agent can't go rogue

**How does the spoken-yes gate actually work?** (`services.find_spoken_approval`)
1. When a draft is created (an order or a stock transfer), we store a **watermark**: the latest id in the append-only `transcript_events` log.
2. `approve_procurement_request` succeeds only if, after the watermark:
   - the **agent spoke** (the read-back), and
   - the worker's **latest final utterance** after that read-back is affirmative (`yes|confirm|submit|go ahead|move it…`) and not negated (`no|wait|cancel|not yet…`).
3. **Split answers.** ASR often splits one reply into several final segments, so all the worker's finals since the agent last spoke are read together. "Yes." followed by "Move it." approves; "Yes." followed by "No, wait." does not.
4. **Order, not clock time.** Ordering uses the event id, not timestamps. "Order it and submit it", spoken before the read-back, can never count.
5. **Transcript lag.** The tool waits up to `APPROVAL_WAIT_S` (4 s) for the yes to arrive through the transcript relay.
6. **Proof is stored.** The matching utterance is saved as `approval_evidence`. The only other path is a human clicking Approve in the console.

**Couldn't the browser fake a "yes"?**
In this prototype, transcripts reach the backend through the signed-in console, so a person with console access could. For production we'd take transcripts server-side, from Agora's webhooks or an RTM server subscription, so the gate never trusts the client. Either way the LLM cannot approve, because the approval tool only checks the worker's own transcript.

**How do you know a write really happened?** (`tools._verify`)
- After every mutation we re-read the row on a **fresh SQLite connection**, which proves the write was committed, and check the expected state, for example `status == "SUBMITTED"`.
- Only then does the result carry `verified: true`, and the prompt forbids saying "done" without it.
- Writes are idempotent where it matters. Orders dedupe on `part_id|work_order` while one is pending or submitted, and reservations don't double-reserve.

**What is the claim guard?** (`guard.py`)
- It runs on every final agent utterance.
- **Action claims** ("submitted", "reserved", "escalated", "posted to the ERP"…) map to the tools that make them true, within a 120 s window.
- **Source claims** ("the manual says", "in stock", "last shift") require the matching lookup tool earlier in the session.
- A negation filter skips offers and questions ("shall I submit?", "I couldn't…").
- On a violation it records a red `claim_guard` evidence item and injects a correction into the live agent.
- **Why it exists:** on 19 Nov, with the MCP server unreachable, the LLM said "the procurement request has been submitted" and quoted a manual section that doesn't exist. Prompting didn't stop it; this does, from outside the model.

**How do you enforce what the agent can do per task?**
- **Twice.** First in Agora's `mcp_servers[].allowed_tools`, so the model never even sees forbidden tools. Then server-side in `tools._check_task_allows` for any call that arrives through MCP.
- A read-only "shift briefing" task can't place an order even if the model hallucinates the tool name.
- Tasks without an explicit list get the 16 `CORE_TOOLS`. The 6 warehouse and training tools are opt-in.

**How are model outputs kept separate from facts?**
- Every evidence row has a `source_type`: `technician`, `camera_model`, `agent_inference`, `tool_result`, `cmms`, `manual` or `claim_guard`.
- Camera readings and hypotheses are never shown as confirmed. Closing a hypothesis requires `update_open_item` with a reason (confirmed, ruled out or answered).

**How is training marked without the LLM?** (`workplace.evaluate_answer`)
- Each question in the pack has `key_points`, each with several acceptable phrasings.
- The trainee's answer is normalised and string-matched. Enough points means correct, some means partly, none means incorrect.
- Score and pass mark are computed in code, and the result is written to `learning_records`. The LLM never receives the answer key.

---

## 3. Reliability and latency

**How did you test with a real voice agent?**
- `scripts/scenarios.py` drives **real Agora sessions** in headless Edge.
- `getUserMedia` is replaced by a canvas camera (panel images, CC photos and videos, with blur, dim and glare effects) and a Web Audio mic that plays synthetic technician lines, optionally over factory noise.
- Each step records the ASR transcript, agent reply, tool calls, evidence, database state and latency, then scores labelled checks.
- 14 scenarios include: approval, barge-in, read-only briefing, failures, noise, safety, recovery, vision, and a real-photo vision dataset.
- 20 scored runs went from 35% of checks passing on the first run to 100% on later full runs.
- 44 failures are logged in `experiments/FAILURES.md` with root cause and fix, and 89 unit and integration tests pin the fixes.

**Give me an example of a failure you fixed.**
1. **#38 Split "yes" (live).** ASR split "Yes. Move it." into two finals, so the gate saw only "Move it.". Fix: read the reply's finals together, with the latest words deciding.
2. **#42 Harness bug.** The built-in test feed replaced the harness's camera, which invalidated one vision run. Fix: the harness turns the feed off, and the run was quarantined.
3. **#43 Missed camera evidence.** The agent said "It looks like you are viewing…" but the capture didn't fire. Fix: wider phrase coverage, plus a test.

**What's the latency, and how do you hide it?**
- End of turn is 640 ms of VAD silence.
- Measured live, the median full turn is about 3.6 s without tools and about 7.0 s with MCP tools.
- To cover tool turns, Agora filler words ("Let me check that.") play through Murf if no speech has started after 1.2 s. That brought first audio down to about 1.75 s. Fillers state intent, never an outcome.

**What happens when something breaks?**
- **Tool errors:** returned as structured `ServiceError`s (for example `inventory_unavailable`, `supplier_rejected`). The prompt makes the agent say what failed and that nothing changed. Failure switches on the System page let you demo this.
- **Tunnel down:** agents get a system notice to stop claiming lookups.
- **Agent dropped:** `voice_monitor` polls the agent status every 15 s, records it in the timeline and offers **Restart voice** with a fresh agent while keeping the session record. The agent's `idle_timeout` is 300 s, to ride out Wi-Fi blips.

---

## 4. Data, integrations and cost

**What's the data model?**
- SQLite in WAL mode, with short-lived connections.
- **Core:** `assets`, `work_orders`, `work_order_log`, `sessions`, `evidence`.
- **Transcripts:** a display table plus the append-only `transcript_events` used by the approval gate.
- **Operations:** `tool_actions` (audit of every call with input, result and duration), `procurement_requests`, `stock_levels` (per location), `stock_transfers`, `erp_postings`, `shipments`, `follow_ups`, `learning_records`, `handoffs`.
- **Integrations:** `integration_events` and `integration_deliveries`.
- **Config:** use cases are packs (`demo_data/packs/<id>/pack.json`) with machines, manuals, limits, safety notes, history and training modules, plus `tasks.json` for session types and tool allowlists.

**How do integrations work?** (`integrations.py`)
1. **Events.** After any tool returns `verified: true`, `run_tool` maps it to a business event (`order.submitted`, `transfer.posted`, `escalation.raised`, `handoff.published`, …) and stores it.
2. **Delivery.** It is delivered asynchronously, so it never blocks the voice turn, to each configured connector. Delivery retries 3 times with backoff, except on 4xx errors other than 429.
3. **Signed webhooks.** Generic webhooks carry `X-Shifttrace-Signature: sha256=HMAC(body)`.
4. **Telegram and WhatsApp.** Telegram uses `sendMessage` and `sendDocument` (the handoff as HTML and XLSX). WhatsApp Cloud API sends a text or template message, uploads the XLSX to `/media`, then sends a document message.
5. **Partial delivery.** If the message went out but the attachment failed, it's marked `partial` and not retried, so there's no duplicate message.
6. **Links and logs.** Messages link back to the handoff and audit log through `PUBLIC_CONSOLE_URL`. Bot tokens never appear in the delivery log.

**How do you compute the cost?** (`costs.py`)
- **Measured per session:** voice and camera minutes come from `usage_segments`, with agent minutes rounded up per task, as Agora bills. Characters spoken and turns are counted too.
- **Projection:** rates are list prices, overridable through `COST_*`:
  - Agora Conversational AI: $0.0099/min
  - ASR: $0.0166/min
  - RTC audio / video: $0.99 / $3.99 per 1,000 min
  - Murf: $0.01 per 1,000 characters
  - gpt-4o-mini: $0.15 / $0.60 per million tokens
- **Per shift:** 40 active minutes comes to about $1.40, versus about $14.60 if streamed for 8 hours.
- **Controls:** idle pause after N silent minutes stops the agent and leaves RTC. The camera can be on-demand (video costs about 4× audio), and push-to-talk is available.

**What's the stack?**
- **Backend:** Python 3.12, FastAPI, the MCP Python SDK (FastMCP), the Agora agent SDK, httpx, SQLite and openpyxl.
- **Frontend:** React 19, Vite, Tailwind v4, the Agora RTC and RTM SDKs, the Agora Voice AI toolkit, three.js / React Three Fiber and ZXing.
- **Tests:** pytest and Playwright.
- **Deploy:** Docker on Render.

---

## 5. Scaling it to a real company

**How would this scale beyond one laptop?**
- The voice and media plane is already Agora's cloud.
- Our side is a stateless API plus MCP server. Swap SQLite for Postgres and run several replicas behind a load balancer. Sessions are keyed by `X-Shifttrace-Session`, so any replica can serve a tool call.
- Move the event bus and integration delivery to a queue.
- Take transcripts from Agora's server-side callbacks instead of the browser relay.

**How would you connect a real CMMS or ERP?**
- The tool layer calls a service module (`services.py` / `workplace.py`). Replace the SQLite-backed functions with API adapters, for example SAP PM or Maximo work orders and SAP MM stock and purchase requisitions.
- Keep the same verify step: read back from the real system before reporting success.
- Outbound, the signed-webhook connector already works with middleware such as Power Automate, n8n or MuleSoft.

**Multilingual?**
- Swap the STT language and Murf voice per site or worker. Murf Falcon has Indian-language voices, and Deepgram supports several languages.
- The tools and records are language-independent. Approval phrases would need localised patterns, which are already isolated in one regex.
