# SHIFTTRACE — Master Agent Mandate and Execution Prompt

**Use:** Paste this entire document into Claude Code / Fable as the primary project brief.  
**Prepared:** 19 November 2026  
**Repository:** Create a new, independent project folder named `shifttrace`.  
**Track:** Build with Agora — Bengaluru 2026, PS31.

---

# PART A — COPY-PASTE AGENT PROMPT

You are joining a time-constrained, solo hackathon build. Operate as a senior product engineer, multimodal AI engineer, realtime communications engineer, backend architect and pragmatic hackathon strategist.

You must do more than propose an architecture. Inspect the environment, read the official documentation, reuse suitable open-source patterns, build a functional vertical slice, run it, test it and document what actually works.

## 1. The objective

Build **SHIFTTRACE**, a voice-first, multimodal maintenance continuity assistant that gives each machine an evidence-backed operational memory across technician sessions and shift handovers.

Our core line:

> The maintenance system remembers the tickets. SHIFTTRACE remembers what actually happened.

This project must satisfy **PS31 — Voice AI at Work: Beyond the Call Center / Field Technician Copilot workflow** from Build with Agora Bengaluru 2026.

The organiser's problem statement is mandatory. We are allowed to be creative in our solution, but we must solve the selected problem.

The required PS31 stages are:

- **Before:** Retrieve assigned tickets, equipment history and maintenance records.
- **During:** Diagnose/troubleshoot through interactive voice conversation.
- **Action:** Check spare-part availability, raise orders, update tickets or escalate through APIs.
- **After:** Generate service reports, update records and initiate follow-ups.

Required technology includes Agora Conversational AI, Agora RTC and/or Chat, Murf AI Falcon TTS, LLMs/RAG, tool calling, MCP-compatible integrations and enterprise APIs.

The demo must show a complete workplace workflow: initiate through voice, understand and retrieve relevant context, execute meaningful actions through APIs, confirm the result and follow up.

### Official event sources

- Event and agenda: https://buildwithagora.knotic.co/
- Track / PS31: https://www.commudle.com/communities/knotic/hackathons/build-with-agora-blr/tracks
- Luma: https://luma.com/2g5vcgrr?tk=8AXBfg
- Agora docs: https://docs.agora.io/en/ai/
- Murf: https://docs.murf.ai/

Event date is 21 November 2026. Check the organiser's latest event page for any timing changes.

## 2. Product concept

SHIFTTRACE preserves the context surrounding maintenance work, not just the final ticket status.

A technician scans/selects an asset, asks what happened previously, starts a live voice/camera session, describes what they observe, retrieves relevant history/manual information, checks parts inventory, requests/approves an action and generates a handoff for the next shift.

It is not a generic maintenance chatbot. The differentiator is **evidence-backed operational memory and continuity across shifts**.

The system must distinguish:

- A visual observation.
- An audio observation.
- A technician statement.
- An authoritative record returned by an API/database.
- A model inference or hypothesis.
- An action requested.
- An action actually executed and verified.

Never present an unverified model inference as a confirmed mechanical diagnosis.

## 3. Product flow to implement

### Step 1 — Identify asset

For the demo, provide a QR code or simple asset selector for a fictional compressor `C-204`.

Retrieve:
- Asset metadata.
- Previous maintenance sessions.
- Open work orders.
- Past observations.
- Parts used/requested.
- Pending action items.

### Step 2 — Start a real voice session

Use Agora Conversational AI as the primary realtime voice interaction layer.

Use Murf AI Falcon TTS through Agora for spoken output.

The application should show:
- Session state.
- Microphone state.
- Camera state if enabled.
- Selected agent/model.
- Live transcript or messages where available.
- Connection/error state.

Do not substitute browser `speechSynthesis`, a different TTS provider or a standalone voice API for the required Agora + Murf path.

### Step 3 — Observe the equipment

Use the browser camera and, where supported by the selected inference path, audio input.

MiniCPM-o 4.5 is our initial multimodal inspiration and should be tested if feasible. However, do not block the hackathon on a large local checkpoint.

Investigate a hosted vision-capable alternative such as Gemini Live if needed. Keep the perception component modular.

At minimum the demo must show a real camera/image observation that influences the workflow. It can be a prepared panel image or controlled live camera view.

If the perception model is separate from Agora Conversational AI, explicitly pass timestamped observations to the agent/backend. Do not claim the Agora LLM directly saw the complete video stream unless this is actually configured and verified.

### Step 4 — Retrieve context

The agent must retrieve real data from our demo backend:

- Previous compressor C-204 work orders.
- Prior shift handoff.
- Relevant maintenance-manual sections.
- Parts inventory.

Use seeded SQLite data so all judges can reproduce the workflow.

### Step 5 — Execute actions

At least two meaningful tool/API calls must occur. Recommended flow:

1. `get_asset_history(asset_id)`
2. `check_inventory(part_id)`
3. `create_procurement_draft(part_id, quantity, work_order_id)`
4. After explicit technician approval: `approve_procurement_request(request_id)`
5. `update_work_order(work_order_id, status, note)`
6. `create_shift_handoff(session_id)`

Make sure the application persists the changes and can show the results.

### Step 6 — Verify and hand off

The agent must verify the actual API/database result before saying the action succeeded.

Generate a concise shift handoff with evidence links/timestamps, completed actions, failed actions, unresolved issues and recommended next checks.

Simulate a second-shift technician asking:

“What happened with C-204? What have we tried, and what still needs attention?”

The answer must come from the stored handoff and source records, not a fabricated free-form summary.

---

## 4. Required Agora and Murf integration

### Agora links

1. Conversational AI Platform overview: https://docs.agora.io/en/ai/platform/overview
2. Create an agent and start a session: https://docs.agora.io/en/ai/platform/get-started/start-stop-agent
3. Agora Vision Recipe: https://github.com/AgoraIO-Conversational-AI/recipe-agent-vision
4. Send images to the agent: https://docs.agora.io/en/ai/build/send-images
5. Custom tools: https://docs.agora.io/en/ai/build/tools/custom-tools
6. MCP tools: https://docs.agora.io/en/ai/build/tools/mcp-tools
7. Custom LLM integration: https://docs.agora.io/en/ai/platform/build/custom-model-integration/custom-llm
8. Release notes: https://docs.agora.io/en/ai/platform/release-notes
9. Pricing: https://docs.agora.io/en/ai/platform/pricing

### Murf Falcon links

1. Murf developer docs: https://docs.murf.ai/
2. Agora's Murf integration: https://docs.agora.io/en/ai/platform/models/tts/murf

Current Agora Murf docs show:

- Murf requires BYOK; it is not available in managed mode.
- The Murf API key must be stored in a secret set and referenced by the agent.
- WebSocket endpoint example: `wss://global.api.murf.ai/v1/speech/stream-input`.
- TTS model field: `FALCON`.
- Example output sample rate: 24,000 Hz.
- Voice ID and locale are configurable.

Inspect the current documentation and SDK. Configure Murf Falcon in the real Agora agent. Verify it audibly. Keep secrets outside source control.

### Agora tool execution caveat

Agora's current custom-tool documentation says custom tools are synchronous GET/POST HTTPS calls; it does not document asynchronous callbacks/polling in this mechanism. Keep tool endpoints short and deterministic. For longer operations, let a tool start a backend task and return a task identifier; have our application/backend manage the task lifecycle rather than relying on unsupported tool callbacks.

MCP is an alternative if the currently documented transport fits the deployment. Check whether the endpoint must be publicly reachable by Agora cloud; do not assume localhost `stdio` can be called remotely.

---

## 5. Open-source repositories to inspect and reuse

Do not clone all repositories blindly. Inspect README, code, dependencies, licence and exact fit. Reuse patterns, not necessarily entire applications.

### Priority 1 — Agora Vision Recipe

https://github.com/AgoraIO-Conversational-AI/recipe-agent-vision

This is the first repository to inspect and likely the quickest starting point.

It demonstrates browser camera and microphone publishing through Agora RTC, an Agora agent backend and a web interface. The current README documents Windows-compatible setup with Python 3.10+, Bun and Agora credentials.

It currently uses a sample LLM/TTS configuration that is not the required Murf Falcon setup. Adapt it and verify Murf Falcon.

### Priority 2 — Agora RPG Recipe

https://github.com/AgoraIO-Conversational-AI/recipe-agent-rpg

Use it to understand a single FastAPI backend, SQLite state, FastMCP tools, public MCP endpoint and voice narration. Replace game-state logic with asset, work-order, inventory and handoff tools.

Do not expose sensitive endpoints. Use demo data and authentication.

### Priority 3 — Realtime-Venus

https://github.com/inclusionAI/Realtime-Venus
https://realtime-venus.github.io/
https://huggingface.co/inclusionAI/Realtime-Venus
https://arxiv.org/abs/2609.13814

Investigate its 9B Omni and Audio models plus asynchronous Harness runtime. It is an interesting open-weight full-duplex audiovisual candidate. Standalone inference requires Python 3.10, CUDA and FFmpeg; repository startup scripts are Linux-oriented. Verify actual hardware feasibility and model/weight terms before attempting downloads.

### Priority 4 — Qwen Audio Agent

https://github.com/QwenAudio/qwen-audio-agent
https://qwenaudio.github.io/qwen-audio-agent/
https://qwenaudio.github.io/qwen-audio-agent/architecture/overview

Use as an architecture reference for realtime frontend/backend agent separation, asynchronous tasks, task lifecycle, MCP and provider adapters. Do not replace Agora as the required conversation layer.

### Priority 5 — MOSS-Live

https://github.com/OpenMOSS/MOSS-Live
https://platform.moss.cn/

Explore as a full-duplex audio/vision and background-task reference. Treat as hosted/API unless downloadable weights and self-hosted inference are independently verified.

### Priority 6 — ERPNext maintenance concepts

https://github.com/frappe/erpnext
https://docs.frappe.io/erpnext/asset-maintenance

Borrow asset and maintenance data-model concepts; do not install full ERPNext during this hackathon.

### Priority 7 — DCASE 2026 sound anomaly research

https://dcase.community/challenge2026/task-first-shot-unsupervised-anomalous-sound-detection-for-machine-condition-monitoring
https://github.com/icerdavid/dcase2026_task2_baseline_ae

Future research only. Do not claim machine sound anomaly detection is a validated diagnosis of a specific fault.

---

## 6. Winning mindset and ideation rules

Be ambitious in the product insight but ruthless about demo scope.

### Rule 1 — Solve PS31 explicitly

A novel experience is not enough if it does not retrieve enterprise information, troubleshoot through voice, execute an action and follow up. Every major feature must map to the PS31 workflow.

### Rule 2 — Don't copy the organiser's example

The Field Technician Copilot is an example of the workflow. SHIFTTRACE should offer a distinct insight: evidence-backed operational memory across shifts.

### Rule 3 — Make the technology essential

Multimodal perception must do something useful that a plain text chatbot cannot. For SHIFTTRACE, it observes the physical equipment and associates timestamped observations with the maintenance history.

### Rule 4 — Show a complete loop

The demo should show: observe → retrieve → reason → act → verify → preserve memory → hand off.

### Rule 5 — Prefer a real small workflow to a fake large platform

One asset, one seeded fault history, one parts inventory, one verified work-order mutation and one handoff are enough. Do not build a large generic CMMS.

### Rule 6 — Build a judge-visible moment

A second-shift technician asks what happened and the assistant can answer immediately with the exact prior observations and actions. This is the “aha” moment.

### Rule 7 — Verify everything

The agent must not claim an order was submitted until the backend returns a successful persisted record. Show the record in the UI.

### Rule 8 — Handle uncertainty honestly

Model output can be wrong. Use labels such as “model observation”, “technician-reported” and “verified system record”. Do not let a visual guess become a safety claim.

### Rule 9 — Measure rather than decorate

Show timestamps, tool results, evidence and a trace of what happened. Avoid fake confidence percentages and fake model status indicators.

### Rule 10 — Keep future scope credible

Real CMMS, ERP, IoT sensors and predictive maintenance can be future integrations. Do not pretend they are already implemented.

---

## 7. Recommended technical architecture

### Frontend

- Next.js/React or the existing frontend in the Agora Vision Recipe.
- TypeScript.
- Agora Web SDK for RTC media.
- Browser camera and microphone permissions.
- Session status, live transcript, event timeline and handoff panel.

### Backend

- Python FastAPI.
- Agora agent/session lifecycle.
- Murf Falcon configuration.
- Tool endpoints or MCP server.
- Perception-worker interface.
- SQLite persistence.
- Audit log.

### Data

- Seed one fictional compressor asset C-204.
- Seed a prior vibration complaint and previous sensor replacement.
- Seed current unresolved work order.
- Seed inventory with required bearing unavailable.
- Seed relevant maintenance manual excerpt.

### Perception worker

Start with the simplest viable approach:

1. Test MiniCPM-o 4.5 if hardware/hosted access permits.
2. If not feasible, test a hosted vision-capable model for the demo.
3. Keep a separate interface for the model so it can be replaced.
4. Return structured, timestamped observations to the application.
5. Do not claim the observer is the Agora Conversational AI model unless the integration truly is configured that way.

### Suggested tools

```text
get_asset_history(asset_id)
get_open_work_orders(asset_id)
search_maintenance_manual(asset_id, query)
check_inventory(part_id)
create_procurement_draft(part_id, quantity, work_order_id)
approve_procurement_request(request_id)
update_work_order(work_order_id, status, note)
create_shift_handoff(session_id)
```

---

## 8. Execution plan and stage gates

Do not spend most of the time writing a long plan. Audit, build and validate in the following order.

### Stage 0 — Inspect current workspace and environment

- Confirm this is a new SHIFTTRACE project directory.
- Do not modify Voxie, MiniCPM Omni Lab or other existing projects.
- Inspect Python, Node/Bun, Git, available storage, CPU/RAM and GPU.
- Inspect existing credentials only by checking whether environment variables are present; never print secret values.
- Create `.env.example` but not a committed `.env`.
- Document blockers.

**Gate:** know the available runtime and required service credentials.

### Stage 1 — Clone and run Agora Vision Recipe

- Clone the official recipe into a reference folder or inspect it without copying unnecessary files.
- Follow its Windows-compatible instructions.
- Obtain Agora credentials through the approved portal/CLI.
- Confirm camera/mic tracks publish.
- Start and stop an agent session.
- Hear a response.

**Gate:** actual Agora voice session works from the browser.

### Stage 2 — Configure Murf Falcon

- Read the current Agora Murf documentation.
- Configure Murf TTS with BYOK and Falcon model.
- Store the secret securely.
- Use a valid voice ID and locale.
- Run a short spoken test.
- Confirm the selected TTS provider in logs/config.

**Gate:** the voice output is actually Murf Falcon through Agora.

### Stage 3 — Create the demo backend and data

Implement SQLite seed data for C-204, history, work order, inventory and manual sections.

Implement and test deterministic APIs for asset history, work orders, manual retrieval, inventory, procurement draft/approval and handoff.

**Gate:** every action works through an API and can be verified in SQLite/UI.

### Stage 4 — Add multimodal observation

- Publish camera frames through Agora RTC using the Vision Recipe pattern.
- Verify how frames are forwarded and to which model.
- Test MiniCPM-o or another suitable model for reading the prepared panel and describing visible evidence.
- Store timestamped observations with provenance.
- Add audio evidence only if the selected path reliably supports it.

**Gate:** at least one real visual observation changes or informs the workflow and is visible in the event timeline.

### Stage 5 — Connect the voice agent to tools

- Implement the smallest useful set of custom tools/MCP tools.
- Ensure descriptions and JSON schemas are precise.
- Add explicit approval before the procurement or other consequential mutation.
- Verify each action's persisted result.
- Demonstrate an error/unavailable-part branch.

**Gate:** complete end-to-end workflow with at least two meaningful tool/API calls and one verified state mutation.

### Stage 6 — Shift handoff

- Generate a structured handoff from persisted evidence and actual action results.
- Store it.
- Start a simulated second-shift session.
- Retrieve and answer from the stored handoff.

**Gate:** second technician can ask what happened and obtain source-backed context.

### Stage 7 — Polish and demo preparation

- Improve the UI only after the pipeline works.
- Display session/agent/model status truthfully.
- Add visible recording indicator and stop control.
- Show evidence timeline and actions.
- Add a resettable demo seed script.
- Prepare a backup prerecorded walkthrough in case network/model service fails.
- Rehearse to 3 minutes.

**Gate:** reliable demo can be repeated from a clean state.

---

## 9. Required project structure

```text
shifttrace/
  README.md
  CLAUDE.md
  CHANGELOG.md
  .env.example
  .gitignore
  docs/
    01_CONTEXT_AND_PRODUCT_STRATEGY.md
    02_TECHNICAL_RESEARCH_AND_REFERENCES.md
    03_AGENT_MANDATE_AND_EXECUTION_PROMPT.md
    ARCHITECTURE.md
    INSTALLATION.md
    DEMO_RUNBOOK.md
    TROUBLESHOOTING.md
  research/
    MODEL_EVALUATION.md
    PERCEPTION_LIMITATIONS.md
    DECISIONS.md
  backend/
    app/
      api/
      tools/
      agora/
      perception/
      services/
      storage/
      schemas/
    tests/
  frontend/
  demo_data/
    seed.sql
    media/
  results/
    runs/
    screenshots/
```

Keep only files that are actually useful. Do not create empty placeholder documentation to make the repository look complete.

---

## 10. Website requirements

The website is a functional technician console, not a marketing page.

Minimum views:

1. **Asset overview:** C-204 details, open work order and maintenance history.
2. **Live session:** Agora conversation controls, camera preview, microphone status, transcript and model observation.
3. **Evidence timeline:** timestamped statements, visual observations, model hypotheses, retrieved records and tool results.
4. **Action panel:** inventory status, procurement draft, approval and work-order update.
5. **Shift handoff:** generated report and query interface for next shift.

The UI must show the real state returned by the backend. Do not fabricate live events, transcripts, model status or tool outcomes.

---

## 11. Demo script

Use the following script unless testing reveals a more reliable flow.

**Opening:** “Every machine has a maintenance history. But the context of what happened during a shift usually gets lost.”

1. Select/scan compressor C-204.
2. Ask: “What happened during the previous shift?”
3. Agent retrieves the prior vibration report and previous action.
4. Start camera and show prepared control panel. Ask: “Can you inspect what is visible here?”
5. Agent reports a visible warning indicator as an observation, not a diagnosis.
6. Technician says: “Check whether the required bearing is available.”
7. Agent checks inventory and reports it is unavailable.
8. Technician says: “Prepare a procurement request and update the work order.”
9. Agent creates draft and asks for approval.
10. Technician approves.
11. Backend persists request and work-order update. UI displays the IDs/statuses.
12. Agent creates shift handoff.
13. Switch to next-shift view and ask: “What happened, what was done and what is still pending?”

Target duration: approximately three minutes. Rehearse and trim if necessary.

---

## 12. Testing and acceptance checklist

### Agora and Murf

- [ ] Browser obtains microphone permission.
- [ ] Browser obtains camera permission.
- [ ] Agora RTC session joins.
- [ ] Agora Conversational AI agent starts.
- [ ] Spoken user input reaches agent.
- [ ] Murf Falcon is configured in Agora.
- [ ] Spoken output is audible.
- [ ] Session stop and cleanup work.

### Perception

- [ ] Real camera/image input reaches the selected observer.
- [ ] Model output is stored as an observation with source and timestamp.
- [ ] It is clear which model produced the observation.
- [ ] The UI does not treat model guesses as confirmed facts.

### Agentic workflow

- [ ] Asset history retrieval works.
- [ ] Maintenance-manual retrieval works.
- [ ] Inventory lookup works.
- [ ] Procurement draft works.
- [ ] Approval is required before submission.
- [ ] Work-order update works.
- [ ] Actual persisted state is verified after each mutation.
- [ ] Failure/unavailable inventory branch works.
- [ ] Handoff is created and saved.
- [ ] Next shift can query the handoff.

### Demo quality

- [ ] Clean reset script works.
- [ ] Three-minute demo is rehearsed.
- [ ] Network/service failure backup exists.
- [ ] Secrets are not in Git.
- [ ] No real private industrial/worker data is used without permission.

---

## 13. Documentation and reporting rules

Create and maintain:

- `README.md` — what the project does, how to run it and demo summary.
- `CLAUDE.md` — project instructions and invariants.
- `docs/ARCHITECTURE.md` — system components and data flow.
- `docs/INSTALLATION.md` — exact setup commands.
- `docs/DEMO_RUNBOOK.md` — exact repeatable demo steps.
- `research/MODEL_EVALUATION.md` — model choices and verified capability matrix.
- `research/PERCEPTION_LIMITATIONS.md` — known limitations and unverified claims.
- `research/DECISIONS.md` — important technical and product decisions.
- `CHANGELOG.md` — notable implementation changes.

For every meaningful integration, record:

- Official source URL.
- Repository commit/release inspected.
- Model and revision.
- Runtime/version.
- Hardware/service used.
- Input used.
- Actual observed output.
- Test result.
- Limitations.

Use status labels:

- `verified-local`
- `verified-hosted`
- `implemented-not-tested`
- `code-reference-only`
- `paper-only`
- `blocked`
- `not-supported`

Never claim a feature works because the code compiles or a UI exists.

---

## 14. Constraints and safety

- Do not modify Voxie or the separate MiniCPM research project.
- Keep SHIFTTRACE independent.
- Do not spend money or call paid services without authorisation.
- Do not expose local services publicly except a narrowly scoped, authenticated endpoint required by Agora; use demo data only.
- Inspect repository scripts before running them.
- Do not download very large model checkpoints before checking VRAM/storage.
- Keep keys in environment variables/secret stores.
- Do not collect real worker recordings without consent.
- Show an explicit recording indicator and stop control.
- Require confirmation for procurement and other consequential actions.
- Do not claim AI diagnoses machine faults.
- Do not claim a tool action succeeded until backend state verifies it.
- Do not build features that cannot be demonstrated.

---

## 15. Definition of success

The project is successful when a judge can:

1. Start a real Agora voice session and hear Murf Falcon output.
2. See the technician's camera input and a real multimodal observation.
3. Ask about a machine's previous maintenance history.
4. Hear a grounded answer based on seeded records.
5. Ask the agent to check spare-part availability.
6. See at least two actual tool/API calls.
7. Approve a procurement/work-order action.
8. Verify the persisted result in the interface/database.
9. Generate a shift handoff.
10. Ask as the next-shift technician what happened and what remains unresolved.

The product is not judged by how many models or features it lists. It is judged by a credible, complete, differentiated workplace workflow.

---

# PART B — FIRST ACTIONS FOR THE AGENT

Start now. Do not ask the user to select a new concept or another model.

1. Confirm/create the independent `shifttrace` directory.
2. Save this mandate and the two companion context/reference documents in `docs/`.
3. Inspect the machine and development environment.
4. Inspect/clone the Agora Vision Recipe and understand its camera/voice flow.
5. Verify Agora and Murf credentials are available without printing secret values.
6. Build and run the smallest real Agora + Murf conversational session.
7. Add the seeded C-204 maintenance data and deterministic APIs.
8. Add the camera/perception path.
9. Complete the procurement/work-order workflow and shift handoff.
10. Build/polish the technician UI.
11. Rehearse the demo and record actual test evidence.

If a dependency or integration is blocked, document the precise cause and move to the smallest viable fallback without misrepresenting the capability.

The first status report must say exactly:

- What environment was inspected.
- Which repository was cloned/inspected.
- Whether Agora session creation works.
- Whether Murf Falcon output works.
- Whether camera frames reach a model.
- Which APIs/tools are implemented and tested.
- What remains blocked.

**Do not stop after writing a plan. Build the working vertical slice.**
