# Changelog

## 0.13.0 (2026-11-21)
- **Premium visual pass** (see `docs/UI_DESIGN.md`, Visual direction v2): calm graphite greyscale with colour only for meaning, one hi-vis accent, Instrument Sans with nameplate-style condensed headings, tonal surfaces and hairlines, one radius scale. Removed gradient text, glows, grid backdrops, fake window dots and heavy white rules.
- **Shell:** new sidebar and a top bar with breadcrumb, live session and system status.
- **Shift board:** instrument-style readings, and a *Needs a person first* block for the machine that most needs someone, with its chain of evidence and one-click test session.
- **Product page:** large display headline, restyled preview, and a new *On the floor* section.
- **3D floor view** (`/floor` and embedded on the product page): a worker walks to C-204, talks to Shifttrace, sees tool calls, camera evidence, a drafted order approved by voice, a label scan, and the handoff going out to the team's tools. Procedural three.js, lazy-loaded, reduced-motion aware.

## 0.12.0 (2026-11-21)
- **More channels, with the record attached** (`app/integrations.py`, `app/reports.py`):
  - **Telegram** (bot): a message with links per event; when a handoff is published the report is attached as HTML and Excel files.
  - **WhatsApp** (Meta Cloud API): text with links; the handoff Excel is uploaded and sent as a document. Template mode for messages outside the 24-hour window.
  - **Excel / Google Sheets**: one flat row per event for a Power Automate flow (Excel Online table) or an Apps Script web app, with report and audit links.
  - **Every message links back** to the handoff report, its Excel file, the session's audit log and the machine (`PUBLIC_CONSOLE_URL`). Follow-ups add **Google Calendar and Outlook** "add event" links (no account connection needed) next to the existing `.ics` files.
  - A delivery whose message went out but whose attachment failed is logged as **partial** and is not retried (so the message is not sent twice). Bot tokens are never stored in the delivery log.
- **Reports**: handoff as a self-contained HTML page and an Excel workbook (`/api/handoffs/{id}/report.html|.xlsx`), and an **operations workbook** (`/api/reports/operations.xlsx`) with sessions (linked to their handoff and audit log), tool calls, orders, transfers, stock by location, follow-ups (with calendar links), learning records and events. Download buttons on the handoff page, Records and Connected systems.
- **Scanning without a scanner**: camera barcode/QR scanning in the browser (Scan button in the sidebar, phone header and the session voice bar), typed codes, and a printable **test labels** page (`/labels`) for machines, parts, bins and shipments. Same handler as Zebra DataWedge / wedge scanners.
- Tests: 89 (Telegram, WhatsApp and spreadsheet delivery with mocked transports, partial delivery, calendar links, report workbooks).

## 0.11.0 (2026-11-21)
- **Running cost under control.** Nothing streams all day; the agent exists only while someone is in a session.
  - **Idle pause:** after N minutes of silence (default 3) the agent is stopped and the browser leaves the call, so nothing is billed. **Resume voice** starts a fresh agent; **Pause** does the same on demand.
  - **Camera on demand:** the camera is off until the worker taps Show camera, then turns off after 60 s.
  - **Push-to-talk:** hold Space, or map the device PTT key to F9.
  - **Live cost meter** per session (agent minutes, camera minutes, characters, estimated tokens) and **System → Running cost**: per minute, per shift and per month projections, versus streaming all shift. Rates are public list prices and overridable with `COST_*`. See `docs/COST_AND_DEVICES.md`.
- **Frontline devices:** barcode and QR scans (Zebra DataWedge keystroke output or any wedge scanner). Scan a machine tag on any page to open it; scan a part, bin or shipment label in a session and the agent looks it up.
- **Product page:** a "Built for the floor, priced for it" section with live cost figures.
- Fixed a harness bug (#42): the built-in test feed replaced the scenario harness's camera, which invalidated one vision run. That run is quarantined in `experiments/scenarios_invalid/`.

## 0.10.0 (2026-11-21)
- **Connected systems** (`app/integrations.py`, Setup → Connected systems): verified actions become events and are delivered to the site's real tools.
  - Connectors: Slack, Microsoft Teams, Jira, GitHub Issues and a generic HMAC-signed webhook (ERP, CMMS, Zapier, Make, n8n). Each is off until its variables are set; deliveries are logged and retried up to three times.
  - A local test receiver verifies the signature end to end without an external account.
  - An `.ics` follow-up calendar, plus "Add to calendar" on each follow-up.
  - Escalations now tell the agent where they were queued, and the agent must not claim anyone read them.
- **Agent quality** page (`/quality`): the improvement loop (run, score, diagnose, fix, pin), the pass rate across 19 live runs, the latest run per scenario, all failures and fixes from `FAILURES.md` (41), and the media dataset with licences.
- **Dataset**: `scripts/fetch_dataset.py` grows the CC-licensed media from Openverse (panels, gauges, conveyors, warehouses, forklifts, HVAC, motors, compressors, displays, plus background audio). Each file is labelled with what a camera should see, and hand-held videos are derived with ffmpeg.
- **Records have history**: seeded orders (submitted, rejected, one pending approval), a reservation, an escalation, a completed stock transfer with its ERP postings, and open follow-ups. The Orders, Reservations and Escalations panels are no longer empty after a reset.
- Failures #37 to #41 logged (stale voice credentials, split ASR yes, guard false positive on drafted transfers, ngrok flapping, shipments endpoint).

## 0.9.0 (2026-11-21)
- **Covers the whole PS31 track, not one use case.** New workplaces on the same engine:
  - **Warehouse and logistics** pack `warehouse_dc` (pick zone DC2-ZB): stock per location, carrier shipments with events, and a cycle-count discrepancy. New tools `track_shipment`, `create_stock_transfer` and `confirm_stock_transfer`. A transfer moves stock and posts an ERP document only after the worker's spoken yes or a console confirm, then is re-read.
  - **Training and onboarding** task on every machine and the zone: `get_training_module`, `record_training_answer` (marked in code against pack key points; the model never sees the key) and `finish_training_module` (score, pass mark, learning record).
  - **Follow-ups** (`schedule_follow_up`, a core tool): what, when and who, with spoken due dates parsed. They appear in the handoff and the spoken summary.
- Task tool sets: core tools by default; domain tools opt-in per task and enforced server-side. `read_only` flag for briefings. The agent persona (worker title, systems) comes from the pack.
- Spoken approval reads a reply that ASR split into several finals together ("Yes." + "Move it."), but the latest words decide ("Yes." + "No, wait." does not approve). This was observed live.
- The claim guard covers the new actions ("moved", "posted to the ERP", "scheduled a follow-up", "learning record updated", shipment tracking). Fixed a false positive on "drafted" for stock transfers.
- The console shows transfer confirmation cards in the session. Records include stock transfers (confirm or cancel), shipments, follow-ups and learning records. The handoff lists follow-ups, and the dashboard counts transfers waiting for a yes.
- The product page has a use-case grid mapped to the track (each case "Try it live") and an Initiate → Understand → Execute → Confirm → Follow up section.
- Optional Agora RESTful API key (`AGORA_CUSTOMER_ID` / `AGORA_CUSTOMER_SECRET`) for Conversational AI REST calls; otherwise App ID + certificate tokens.
- Tunnel: ngrok on a static domain no longer restarts on short network blips, and retries "endpoint already online" after a restart.
- New test-feed lines for warehouse and training, plus a warehouse status-board scene.
- Tests: 73 backend tests. The live check `scripts/workflows_check.py` PASS for both the warehouse workflow (transfer TR-6001 done by voice, ERP-70001) and the training workflow (50%, needs review).

## 0.8.0 (2026-11-21)
- **Product page at `/`**, aimed at judges and first-time visitors:
  - Hero: "Every shift hands over. Nothing gets lost." It has an animated product preview built from real C-204 data: technician speech, a lookup, a camera reading with the panel frame, an AI hypothesis, the approval card, the spoken yes and the verified order.
  - A strip naming what is real (Agora, Murf, vision, MCP tools, re-read writes).
  - A four-step "How it works".
  - A "Proof, not chat" grid: sources on every line, the spoken-yes gate, re-read writes, the claim guard, packs and tasks.
  - A comparison against CMMS and field-service apps and voice copilots.
  - Live numbers from the database, which update while a session runs.
  - One-click live sessions on each scenario.
  - **Try the live demo** starts a voice session with the test feed.
- The console moved to `/board`, with a **sidebar app shell**: Shift board; Records (Audit log, Orders and stock, Handoffs); Setup (System and demo, Product page); and the on-shift person, status and theme at the bottom.
- **Shift board redesigned as an operations dashboard:**
  - **Live now** banner.
  - KPI cards: live sessions, machines needing attention, open questions, verified changes.
  - A pending-approvals banner.
  - Machine cards showing what was left open.
  - A live activity feed of tool calls with their outcome, and recent handoffs.
- Type changed to Geist and Geist Mono, with a refined dark palette and a teal-to-sky brand mark.

## 0.7.0 (2026-11-21)
- **Session console rebuilt as a focused three-panel workspace** (modelled on the reference mockup, with corrections):
  - **Left:** machine context, with an Overview tab (make, model, work order, previous shift, still open) and a Safety and manual tab (safety notes, reading limits, manual).
  - **Centre:** the session trace. Each entry has an icon node and a source tag (Speech, Agent, Lookup, Camera unverified, AI hypothesis, Verified change, System record, Claim check failed), and camera frames appear inline.
  - **Right:** the machine camera with test-feed scenes, and Handoff so far.
  - **Bottom:** a voice bar that is always visible: live level waveform, agent state, a large mic button, camera, Capture evidence (asks the agent to record what the camera shows), typing, and the test feed's next line.
  - The approval card is pinned under the trace, with "Say yes to approve" plus Approve and Decline buttons.
  - The page has no site navigation: Shift board on the left, Finish and hand over on the right, and one session timer.
- Corrections to the mockup:
  - AI analysis is shown as an unverified hypothesis, not with a green tick.
  - There is one way to finish instead of two end buttons.
  - The approval card has on-screen buttons as well as voice.
  - Machine data stays fictional (no real brands or models).
- Navigation cut to **Shift board** and **Records**. Records holds Audit log, Orders and stock, and Handoffs as tabs; System stays in the header.
- The Shift board leads with **Live now** when a session is running. Otherwise it shows **Try a test session**, which starts a voice session with the test feed in one click.
- Dark operations theme is now the default; the light logbook theme is one click away.

## 0.6.0 (2026-11-21)
- **Test feed: try it without a machine.** On a machine page, "No machine here? Use the test feed" (on by default) swaps the camera for recorded panels and CC-licensed photos of that machine, and adds **Say for me** buttons that play recorded questions into the microphone. Your own mic stays mixed in. The real Agora agent hears and sees these exactly like a technician on the floor, so tools, approvals, the claim guard and the audit log all run for real.
- Scenes and lines are configuration in `demo_data/testkit.json`, filtered by machine and task. Media come from `experiments/media`. New endpoints: `/api/testkit` and `/api/testkit/media/<file>`, which serves only the files listed in the test kit.
- A line that needs the camera switches to its scene and holds it for 4.5 s before speaking, because frames reach the model late.
- The live camera preview is no longer mirrored, so panel text reads correctly.
- New `scripts/testfeed_check.py` (live, real agent) and 3 new backend tests (62 total).

## 0.5.0 (2026-11-21)
- Rebuilt the console around **one trace**. Speech, lookups, evidence, verified changes and approvals for a session appear in one ordered log with a "now" marker. They were previously split across three columns.
- **Handoff so far** fills in live during the session. **Finish and hand over** writes the handoff, ends the session and opens it.
- Sessions start from the machine page without a form. Who is on shift is set once in the header. Handing over at the end of a handoff starts the next technician's briefing in one step.
- The Shift board shows each machine's actual open questions from the last handover, not just a count.
- New look based on a shift logbook: a time column, ruled shift bands, a continuous trace line, Atkinson Hyperlegible Next type, 24-hour times, and ink colours only for state and provenance. The handoff is drawn as a filed sheet. See `docs/UI_DESIGN.md`.
- UI smoke follows the new flow (board, machine, start, approve, finish and hand over). 0 console errors with and without real voice.

## 0.4.0 (2026-11-21)
- Console redesign along high-performance HMI lines (ISA-101): neutral grey canvas, colour only for abnormal states and provenance, and every state shown as colour + shape + word. Self-hosted Barlow type. Light and dark themes. See `docs/UI_DESIGN.md`.
- New **Audit log** page (`/audit`): every tool call in plain words, filterable by result, actor, session and text, with an inspector for the raw input and result. Verified only after a fresh-connection re-read.
- New **System** page (`/system`): live checks, failure switches and reset moved off the Machines page. A header status button shows problems at a glance.
- Machines lists machines needing attention first and shows each one's last handoff headline. The live session shows the agent's state prominently, approval cards above the conversation, and evidence, tool calls and task steps in tabs. Handoffs read as a document, with "Needs attention" first and a print button. Parts and orders pins pending approvals at the top.
- Provenance marks (shape-coded source glyphs) shared across the session record, machine history and handoffs, with a legend.
- Mobile: two-row header with scrollable navigation, large camera and mic controls, and a bottom-sheet start dialog.
- `record_observation` and `update_open_item` now re-read their write on a fresh connection and return `verified`. If the read-back fails, the call is reported as failed, and the agent is told not to claim the item was recorded. Before this, they were the only write tools without a read-back. 3 new tests.
- UI smoke updated for the new layout, with new screenshots: audit log, audit inspector, system, and dark mode. 0 console errors, including with real voice.

## 0.3.0 (2026-11-21)
- Configurable use cases. The seed now loads data packs from `demo_data/packs/*` (selected with `SHIFTTRACE_PACKS`). The C-204 story moved into `compressor_house` unchanged, plus two new synthetic packs: `packaging_line` (conveyor CV-310) and `building_hvac` (air handler AHU-3), each with its own manual, parts, history, handoff and simulated panel.
- Session tasks from `demo_data/tasks.json`: troubleshoot, preventive maintenance, inspection round, shift briefing (read-only tools). Chosen in the start dialog; stored on the session (`sessions.task_id`, auto-migrated); they drive the agent prompt, greeting and tool allowlist (enforced in Agora `allowed_tools` and server-side), and are written into the handoff.
- Safety reminders come from each machine's `metadata.safety_notes` instead of a hard-coded C-204 line (prompt and handoff composer).
- `/panel/<asset_id>` renders any machine's panel from its pack. New endpoints `/api/packs`, `/api/tasks?asset_id=`.
- New MCP tool `record_reading`: numeric readings are checked against per-machine limits in the pack (`metadata.limits`) in code, and out-of-limit readings are logged as open items. Added after gpt-4o-mini called 12.4 A "above" a 10 to 13 A normal band in a live run.
- Restricted tasks remove the instructions for actions they cannot do from the prompt (live: a briefing agent offered to draft an order).
- Fix: capture and claim-guard dedupe keys are cleared when a session ID is reissued after a reset (live: every vision capture in a full-suite run was silently skipped).
- Tests: 53 backend tests (25 new for packs, tasks, readings and dedupe), UI smoke covers the task picker and the other panels, and there are 3 new live scenarios (`pm_conveyor`, `inspection_hvac`, `briefing_readonly`).

## 0.1.0 (2026-11-19)
- Backend: SQLite demo CMMS (assets, work orders, sessions, evidence with provenance, parts, reservations, procurement, escalations, tool audit, transcripts, handoffs, manual), seeded C-204 story.
- 14 MCP tools for Agora ConvoAI with bearer auth, session binding, verification re-reads and audit log.
- Approval gate tied to the technician's own transcribed words after the read-back; console approval with `think` injection.
- Deterministic shift handoff composer; next-shift retrieval.
- Agora agent lifecycle (managed Deepgram + gpt-4o-mini vision, Murf FALCON, MCP, RTM).
- Auto Cloudflare quick tunnel for the MCP port with startup self-test; credential preflight script.
- Console: Machines, Machine memory, Live session, Action centre, Handoffs, simulated KS-75 panel.
- Tests: 13 backend tests; headless Edge UI smoke with screenshots.
