# SHIFTTRACE — Technical Research, Documentation and Open-Source Reference Pack

**Prepared:** 19 November 2026  
**Purpose:** A verified starting point for implementing SHIFTTRACE under PS31  
**Research rule:** Links and capability notes below are a starting point. Re-check current docs, model revisions, prices, SDK versions and licences before implementation.

---

## 1. Recommended technical strategy

Do not choose a single “best” multimodal model and build everything around it.

For this hackathon, use a layered system:

1. **Agora Conversational AI** for the required realtime voice interaction.
2. **Murf Falcon TTS** as the required voice output provider.
3. **Agora RTC / Vision Recipe pattern** to publish the technician's microphone and camera into the session.
4. **A separate perception worker** for visual context and optional sound-event analysis. Test MiniCPM-o 4.5 first because it inspired the project; evaluate a hosted model such as Gemini Live if local inference is infeasible.
5. **Backend agent orchestration** for maintenance retrieval and tool execution.
6. **SQLite-backed demo CMMS and inventory API** to make the workflow persistent and testable.
7. **Evidence timeline and handoff store** for continuity across shifts.

Important design constraint: do not assume Agora Conversational AI automatically understands arbitrary continuous video from a custom multimodal model. The official Agora Vision Recipe demonstrates camera publishing and forwarding frames into its configured LLM path. If using a separate MiniCPM/Gemini worker, build an explicit integration boundary and timestamp its observations.

---

## 2. Agora — official documentation

### 2.1 Conversational AI Platform overview

https://docs.agora.io/en/ai/platform/overview

Use this as the platform entry point. Confirm current platform/API version and whether the account/project is configured for the Preview or Main documentation set.

### 2.2 Create an agent and start a session

https://docs.agora.io/en/ai/platform/get-started/start-stop-agent

Key concepts from the current docs:

- An **agent** is a saved configuration in the Agora project.
- A **session** runs that agent in an RTC channel or telephony session.
- The business server creates/configures the agent, starts sessions and stops them.
- The current docs provide Python, TypeScript, Go and REST API paths.

Implementation tasks:

- Create or configure the agent once where supported.
- Start a session from the backend.
- Keep Agora credentials server-side.
- Issue RTC tokens from the backend.
- Stop sessions and clean up resources reliably.
- Surface session status and errors in the UI.

### 2.3 Quickstart / client and backend

https://docs.agora.io/en/ai/voice-agent/quickstart

If the URL changes, navigate from the Agora Conversational AI docs' Quickstart section.

### 2.4 Agora Vision Recipe — highest-priority reference repository

Repository: https://github.com/AgoraIO-Conversational-AI/recipe-agent-vision

Current README: https://github.com/AgoraIO-Conversational-AI/recipe-agent-vision/blob/main/README.md

Licence: MIT (verify in the repository's LICENSE before copying code).

What it demonstrates:

- Browser obtains local microphone and camera tracks.
- Browser publishes microphone and camera into an Agora RTC channel.
- Backend handles Agora credentials and agent-session lifecycle.
- Agent receives voice and visual context and responds through the voice pipeline.
- Repo contains a web frontend and Python/FastAPI backend.

The README says it works on macOS, Linux and Windows and documents Python 3.10+, Bun, Agora App ID/App Certificate and camera permission. Basic run flow in current README:

```bash
bun run setup
agora login
agora project use <your-project>
agora project env write server/.env.local
bun run dev
```

Then open `http://localhost:3000`, start a conversation and grant camera access.

What to inspect before reuse:

- `web/` camera/microphone capture and RTC publishing.
- `server/` session lifecycle and agent configuration.
- Which model and TTS provider the example currently configures.
- How visual frames are selected and forwarded.
- Whether video is continuous or sampled/latest-frame based.
- How transcripts and RTC events reach the UI.

Do not assume this example already meets the hackathon's Murf requirement. Its current README describes a managed GPT-4o-mini/Deepgram/MiniMax example configuration. Adapt and verify Murf Falcon.

### 2.5 Send images to the agent

Find the current “Send images to the agent” guide in Agora Conversational AI docs:

https://docs.agora.io/en/ai/build/send-images

If that URL redirects or changes, locate it under Conversational AI → Build → Send images to the agent.

Use it to verify the supported visual input flow, frame format, frame rate, payload constraints and which LLM/MLLM configurations accept images. Do not assume the camera track itself is automatically visible to every model backend.

### 2.6 Murf Falcon TTS integration through Agora

Official Agora guide:

https://docs.agora.io/en/ai/platform/models/tts/murf

The current Agora guide was updated 30 October 2026 and documents Murf as a TTS provider for Conversational AI Platform agents.

Critical facts:

- Murf supports **BYOK only** in this integration; it is not available in Agora managed mode.
- Store the Murf API key in an Agora secret set and reference it from the agent.
- The documented streaming endpoint is `wss://global.api.murf.ai/v1/speech/stream-input`.
- The documented example sets `model="FALCON"` / `model: 'FALCON'`.
- Example fields include `voice_id`/`voiceId`, locale, rate, pitch and sample rate.
- The documented example uses 24,000 Hz sample rate.

Illustrative Python SDK configuration from the official guide (adapt to the current SDK version and secret-set name):

```python
from agora_agent import Agent, MurfTTS, secret_ref

agent = (
    Agent(client=client)
    .with_stt(...)  # configure supported ASR
    .with_llm(...)  # configure supported LLM
    .with_tts(
        MurfTTS(
            key=secret_ref("hackathon_secrets", "murf_api_key"),
            base_url="wss://global.api.murf.ai/v1/speech/stream-input",
            voice_id="Matthew",  # verify available voice IDs in the account
            locale="en-US",
            rate=0,
            pitch=0,
            model="FALCON",
            sample_rate=24000,
        )
    )
)
```

Do not hardcode keys. The voice ID above is an example from the documentation, not a requirement. Verify the actual available Falcon voice IDs and language support in the Murf account/docs.

Murf resources:

- Murf product: https://murf.ai/
- Murf developer docs: https://docs.murf.ai/
- Agora Murf integration: https://docs.agora.io/en/ai/platform/models/tts/murf

### 2.7 Agora custom tools

Official guide:

https://docs.agora.io/en/ai/build/tools/custom-tools

The current guide documents JSON-Schema function definitions and HTTPS endpoints. Important limitations listed in the guide:

- Custom tools support synchronous `GET` and `POST` requests.
- `PUT`, `PATCH` and `DELETE` are not supported by this custom-tool mechanism.
- Asynchronous tools, callbacks, polling and stored/reusable tool references are not supported by this custom-tool mechanism.
- Endpoint must be HTTPS.
- Tool parameter schema is JSON Schema.
- The current docs describe a maximum of 32 tools exposed to the LLM.

Implication for SHIFTTRACE:

- Use compact synchronous tools for simple actions: retrieve asset history, look up inventory, fetch manual chunks, create a draft request, update a work order.
- If a longer operation is required, use a short synchronous tool to create/start a task in our backend, return a task ID, and let the application/backend manage its lifecycle outside the Agora synchronous tool call. Do not pretend Agora custom-tool callbacks/polling exist.
- Handle authentication, idempotency and action authorisation in our own server.

### 2.8 Agora MCP tools

Official guide:

https://docs.agora.io/en/ai/build/tools/mcp-tools

The guide describes Agora Conversational AI acting as an MCP client: the agent can invoke tools exposed by an MCP server, and the server response is returned to the model as context for the next reply.

Use MCP if it reduces integration work and the tool server can be exposed securely over the documented supported transport. Verify the current transport and endpoint requirements before implementation. Do not assume arbitrary local `stdio` MCP servers can be reached by Agora cloud.

### 2.9 Agora custom LLM integration

Official guide:

https://docs.agora.io/en/ai/platform/build/custom-model-integration/custom-llm

The guide says Agora integrates custom LLM services through an OpenAI Chat Completions-compatible HTTP interface and supports SSE streaming. This may be useful for custom reasoning adapters, but does not imply that an arbitrary multimodal streaming model can be wrapped without adapting its protocol, timing and input semantics.

### 2.10 Agora release notes and pricing

- Platform release notes: https://docs.agora.io/en/ai/platform/release-notes
- Pricing: https://docs.agora.io/en/ai/platform/pricing
- RTC Web SDK docs: https://docs.agora.io/en/3.x/api-ref/web_ng/index.html

Check current product and pricing before the event. Do not use a stale tutorial as the definitive API specification.

---

## 3. Murf — official resources and implementation notes

### Required hackathon integration

The hackathon requires Murf AI Falcon TTS for spoken output. Do not satisfy this with browser speech synthesis, MiniCPM's own voice output or another TTS service alone.

### Correct architecture for the submission

- Agora Conversational AI handles the real-time conversational agent session.
- Murf Falcon is configured as the agent's TTS provider through Agora's Murf integration.
- The agent's response text is rendered to speech by Murf and delivered through the Agora session.
- Verify audible output from the real Murf Falcon provider in the actual demo.

### Preflight checklist

- [ ] Murf account/key is available.
- [ ] Agora project credentials are available.
- [ ] Murf key is stored in an approved secret store / environment, not committed.
- [ ] Agora TTS config sets vendor `murf`.
- [ ] Model is set to `FALCON`.
- [ ] Correct websocket endpoint is used for the account/region.
- [ ] Voice ID is valid.
- [ ] Locale is valid.
- [ ] Sample rate and audio format are compatible.
- [ ] A short test phrase is spoken through the complete Agora session.
- [ ] Logs prove Murf is the selected TTS provider.

Do not assume a normal Murf direct API request is equivalent to Agora's supported Murf provider configuration. The hackathon calls for the Agora/Murf path.

---

## 4. Model research candidates

The purpose of model research is to improve multimodal perception and agent experience, not to replace Agora and Murf in the required interaction flow.

### 4.1 MiniCPM-o 4.5 — original inspiration and baseline

- Hugging Face: https://huggingface.co/openbmb/MiniCPM-o-4_5
- Main repo: https://github.com/OpenBMB/MiniCPM-V
- Official demo repo: https://github.com/OpenBMB/MiniCPM-o-Demo
- Official demo site: https://minicpmo45.modelbest.cn/
- Technical docs: https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/minicpm_o4dot5_en.md
- Realtime API docs: linked from the official demo repository.

The official demo repository describes MiniCPM-o 4.5 as a 9B end-to-end model based on SigLip2, Whisper-medium, CosyVoice2 and Qwen3-8B. It supports simultaneous continuous audio/video input with concurrent text/speech output in full-duplex mode.

Use it as the starting multimodal experiment. Do not assume the model can directly call Agora tools or that all multilingual speech capabilities are supported equally. Its official PyTorch/CUDA demo has substantial hardware requirements. Verify the actual runtime against the machine.

### 4.2 Realtime-Venus — high-priority open-weight candidate

- Project: https://realtime-venus.github.io/
- GitHub: https://github.com/inclusionAI/Realtime-Venus
- Hugging Face: https://huggingface.co/inclusionAI/Realtime-Venus
- Paper: https://arxiv.org/abs/2609.13814

Current official repository describes:

- Realtime-Venus-Omni (9B): streaming audio/video, proactive interaction and native speech generation.
- Realtime-Venus-Audio (9B): spoken interaction, audio understanding and native speech generation.
- Realtime-Venus-Harness: shared runtime for delegated tasks and returning results into the originating conversation.

The paper/project describes full-duplex interaction and asynchronous delegation. Repository includes code for the Harness and a browser demo. Standalone inference requires Python 3.10, CUDA and FFmpeg. The install instructions are Linux-oriented (`install.sh`, `start.sh`); evaluate Windows/WSL compatibility rather than assuming native Windows setup is trivial.

The GitHub repo exposes an Apache-2.0 LICENSE file, but inspect the LICENSE and separate model-weight terms before redistribution or commercial use.

**Why relevant:** It provides an interesting pattern for keeping realtime interaction running while background work happens. The hackathon should still use Agora/Murf for the required user interaction.

### 4.3 MOSS-Live — hosted experience and architecture reference

- GitHub: https://github.com/OpenMOSS/MOSS-Live
- Live platform: https://platform.moss.cn/
- Project page: https://www.moss.cn/

The public README describes full-duplex conversation, interruption handling, live visual understanding, selective attention and background tool use. Its architecture separates a foreground interaction model from a background model for reasoning and tool calls.

Treat as an online experiment and architectural reference unless independently verified downloadable weights and self-hosted inference are found. The existence of a public GitHub README does not by itself prove that all production inference weights or services are open-source.

### 4.4 Qwen Audio Agent — orchestration/runtime reference

- GitHub: https://github.com/QwenAudio/qwen-audio-agent
- Docs: https://qwenaudio.github.io/qwen-audio-agent/
- Architecture: https://qwenaudio.github.io/qwen-audio-agent/architecture/overview

The current README shows v2.1.0 dated 10 November 2026, adding Qwen Audio 3.1 Realtime and unified frontend configuration. It separates realtime frontend interaction, orchestration runtime and backend agent. Its docs list multiple frontend options including Qwen realtime audio, Qwen Omni realtime, StepAudio realtime, GPT-Live, Google Live and MiniCPM-o.

Use it to study:

- Provider separation.
- Frontend/backend agent split.
- Task lifecycle management.
- MCP and OpenAPI tools.
- Result delivery while the conversation continues.
- Logs and diagnostics.

Do not make it a mandatory dependency. The hackathon voice transport must still use Agora Conversational AI.

### 4.5 Google Gemini Live

- Live API docs: https://ai.google.dev/gemini-api/docs/live
- Model documentation/pricing: https://ai.google.dev/gemini-api/docs/pricing

A candidate hosted realtime audio/video model. Check current model identifier, input frame constraints, function calling support, pricing, free-tier data handling and region/availability before using. Keep the service optional and avoid uploading private industrial footage without approval.

### 4.6 Other models to investigate only if useful

- OpenBMB MiniCPM family: https://github.com/OpenBMB/MiniCPM-V
- Qwen model family: https://github.com/QwenLM
- StepFun Step-Audio: https://github.com/stepfun-ai/Step-Audio2
- Kyutai Moshi: https://github.com/kyutai-labs/moshi
- OpenMOSS: https://github.com/OpenMOSS
- Meta Seamless Communication: https://github.com/facebookresearch/seamless_communication

Avoid model sprawl during the hackathon. Integrate one perception path that works.

---

## 5. Open-source implementation references for SHIFTTRACE

### 5.1 Agora Vision Recipe — clone and inspect first

https://github.com/AgoraIO-Conversational-AI/recipe-agent-vision

**Use for:** browser camera/mic capture, Agora RTC publishing, agent lifecycle, FastAPI backend and a web interface.

The README currently provides Windows-compatible setup. It is the most direct reference for combining the camera and voice in an Agora conversational session.

### 5.2 Agora RPG Recipe — tool orchestration and SQLite

https://github.com/AgoraIO-Conversational-AI/recipe-agent-rpg

**Licence:** MIT (verify repository LICENSE).  
**Use for:** FastMCP tools, SQLite-backed state, a single FastAPI backend, tool invocation and spoken narration.

The README explains a flow where Agora's cloud agent invokes an in-process FastMCP server through a public Streamable HTTP endpoint. The example uses six game tools backed by SQLite. This is a useful structural pattern for a small CMMS demo, but replace game mechanics with asset history, parts inventory, work orders and handoff.

Caution: the README requires a publicly reachable MCP endpoint (for example, a tunnel) for Agora cloud to call it. Never expose an unauthenticated or sensitive service. Use demo data and narrow endpoints.

### 5.3 Realtime-Venus

https://github.com/inclusionAI/Realtime-Venus

**Use for:** continuous multimodal interaction and background delegation architecture. Do not assume this model can be wired directly into Agora or run on the laptop; verify runtime and interface compatibility.

### 5.4 Qwen Audio Agent

https://github.com/QwenAudio/qwen-audio-agent

**Use for:** separate frontend conversational model and backend task agent, task lifecycle, model provider abstraction and MCP integration patterns.

### 5.5 ERPNext asset maintenance model

- GitHub: https://github.com/frappe/erpnext
- Asset maintenance docs: https://docs.frappe.io/erpnext/asset-maintenance

**Use for:** understanding realistic asset/maintenance concepts and fields. Do not install all of ERPNext for the hackathon. Borrow a small compatible data model for the demo CMMS.

### 5.6 DCASE 2026 — anomalous sound detection

- Task page: https://dcase.community/challenge2026/task-first-shot-unsupervised-anomalous-sound-detection-for-machine-condition-monitoring
- Baseline: https://github.com/icerdavid/dcase2026_task2_baseline_ae

**Use for future research:** machine-condition anomalous sound detection, datasets and baselines. The task detects anomalous sounds relative to normal training recordings; it does not automatically diagnose a specific mechanical fault. Not required for the hackathon prototype.

---

## 6. Proposed demo data model

A compact SQLite schema is enough.

### Assets

- `asset_id`
- `asset_tag`
- `name`
- `manufacturer`
- `model`
- `location`
- `status`

### Maintenance sessions

- `session_id`
- `asset_id`
- `technician_id`
- `started_at`
- `ended_at`
- `summary`
- `status`

### Evidence events

- `event_id`
- `session_id`
- `asset_id`
- `timestamp`
- `event_type`
- `source_type`
- `description`
- `payload_json`
- `model_id`
- `confidence_or_status`
- `verified_by_technician`
- `media_reference`

### Work orders

- `work_order_id`
- `asset_id`
- `status`
- `issue_summary`
- `priority`
- `created_at`
- `updated_at`

### Parts inventory

- `part_id`
- `name`
- `quantity_available`
- `location`
- `reorder_threshold`

### Procurement requests

- `request_id`
- `part_id`
- `quantity`
- `status`
- `created_by`
- `approved_by`
- `created_at`

### Shift handoffs

- `handoff_id`
- `asset_id`
- `source_session_id`
- `created_at`
- `report_json`
- `status`

---

## 7. Agent tools and action semantics

Recommended small tool set:

| Tool | Type | Notes |
|---|---|---|
| `get_asset_history(asset_id)` | Read | Return prior sessions and relevant work orders. |
| `get_open_work_orders(asset_id)` | Read | Return active work. |
| `search_maintenance_manual(asset_id, query)` | Read | Return sourced manual sections. |
| `check_inventory(part_id)` | Read | Return current demo stock. |
| `create_procurement_draft(part_id, quantity, work_order_id)` | Draft/write | Creates a pending request; not submitted. |
| `approve_procurement_request(request_id)` | Mutating | Only after explicit user approval. |
| `update_work_order(work_order_id, status, note)` | Mutating | Use only permitted status transitions. |
| `create_shift_handoff(session_id)` | Write | Generate and persist an evidence-linked handoff. |

Use a single endpoint per custom Agora tool if using the synchronous custom-tool path. MCP can be used if its remote transport and current Agora requirements fit the implementation.

For mutations:

- Require a valid user/technician identity in session context.
- Validate asset and work-order ownership/scope.
- Use idempotency keys.
- Audit who requested and approved the action.
- Return authoritative database state.
- Verify action result before spoken confirmation.

---

## 8. Technical risks and integration caveats

### Agora custom tool limitations

The current Agora custom-tool guide says its custom tools are synchronous GET/POST requests to one HTTPS endpoint. It does not support async tool callbacks, polling or reusable tool references. Do not design a long-running tool call around an unsupported callback mechanism.

### Camera and model split

The Agora Vision Recipe forwards camera frames to its configured vision-capable model. If MiniCPM or Gemini is used as a separate observer, it may need a separate stream or sampled frame worker. Preserve timestamps and do not imply that the Agora voice LLM directly saw all video frames.

### MiniCPM-o 4.5

The official demo repository describes a full-duplex PyTorch+CUDA implementation. Check the machine's GPU/VRAM and supported runtime. Don't let local model setup block the entire demo. Use an explicitly labelled hosted or alternative observer if needed, but keep Agora and Murf in the required conversational path.

### Realtime-Venus

The official repository exposes Apache-2.0 source code and model components, but its standalone inference path requires CUDA and FFmpeg and its shell-based quick start is Linux-oriented. Verify model-weight terms and hardware before downloading or trying to run.

### Privacy

Use synthetic equipment, fake maintenance data and test images for the hackathon. Do not record real workers or real industrial facilities without permission. Show recording status and provide a stop control.

---

## 9. Priority order for repository inspection

1. **Agora Vision Recipe:** quickest route to a real camera+voice Agora web session.
2. **Agora Murf TTS docs:** configure Falcon in the actual agent and verify speech output.
3. **Agora custom tools or MCP docs:** connect asset, inventory and work-order APIs.
4. **Agora RPG Recipe:** learn its SQLite + FastMCP + single-backend tool pattern.
5. **MiniCPM-o 4.5:** test as the first multimodal perception engine if hardware or hosted access permits.
6. **Realtime-Venus / MOSS-Live / Qwen Audio Agent:** inspect as advanced alternatives and architecture references; do not integrate them all.
7. **ERPNext docs:** borrow maintenance vocabulary and data model.
8. **DCASE 2026:** future acoustic anomaly research, not a hackathon dependency.

---

## 10. Source freshness and verification ledger

The links above were checked on 19 November 2026. Before copying code or choosing a model, the implementation agent must re-check:

- Current default branch and recent commits.
- Licence file and model-weight licence separately.
- API version and SDK release.
- Installation requirements.
- Whether a demo is local, hosted or partially mocked.
- Whether a capability is supported by the code or only claimed in a paper/README.
- Current API pricing and data-use policy.

A public repository can contain a demo frontend without containing the full inference weights or production backend. Mark each integration as `verified-local`, `verified-hosted`, `code-reference-only`, `paper-only`, `not-tested` or `blocked`.
