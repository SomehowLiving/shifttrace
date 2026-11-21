# Project status: 21 Nov 2026 (configurable use cases; full live suite on a stable network)

## New: premium UI pass and 3D floor view (21 Nov)
- New visual system (hi-vis accent, Instrument Sans, calm greyscale), new shell, rebuilt shift board and product page hero, and a 3D floor view at `/floor` (also on the product page).
- Verified by screenshots at desktop and phone width (dark and light), 0 console errors; `tsc` and `vite build` pass. The 3D view was checked in software rendering, where it runs slower than on a real GPU.

## New: Telegram, WhatsApp, Excel, calendar links, reports, camera scanning (21 Nov)
- Connectors added: Telegram (message + handoff report attached as HTML and Excel), WhatsApp Cloud API (text + Excel document), and Excel / Google Sheets (a row per event via Power Automate or Apps Script). Every message links back to the handoff, audit log and machine; follow-ups carry Google/Outlook add-to-calendar links.
- Reports: handoff HTML and Excel, plus an operations workbook. Download buttons on the handoff page, Records and Connected systems.
- Scanning without hardware: camera barcode/QR scanner in the browser, typed codes, and printable test labels at `/labels`.
- Verified: 89 backend tests pass (connector deliveries with mocked transports). Not yet sent to a real Telegram, WhatsApp or Power Automate account: that needs those credentials in `backend/.env`.

## New: cost controls and frontline devices (21 Nov)
- Idle pause, manual pause and resume, camera on demand, push-to-talk, a per-session cost meter and per-shift projection. Barcode and QR scans for Zebra DataWedge or wedge scanners.
- 81 backend tests pass. A live check of the pause and resume path is still needed on a real call.

## New: connected systems, agent quality, dataset, record history (21 Nov)
- Verified actions now become events delivered to Slack, Teams, Jira, GitHub or signed webhooks once configured.
  - Checked end to end with the local test receiver: a follow-up scheduled from a session was delivered with a valid signature, and the event log shows it.
  - Not yet tested against a real external account: that needs your Slack, Teams, Jira or GitHub credentials in `backend/.env`.
- The Agent quality page reads 19 live runs, 41 logged failures and fixes, and the media dataset.
- The records pages show seeded history (orders, reservation, escalation, transfer, ERP postings, follow-ups).
- Tests: 78 backend tests pass.

## New: the whole track, not one use case (21 Nov)
- Workflows for field technician (C-204), factory floor (CV-310), facilities inspection (AHU-3), **warehouse and logistics (DC2-ZB)**, **training and onboarding (any asset)** and **follow-ups (all tasks)**. 21 MCP tools.
- Verified live with real Agora and Murf, using the test feed:
  - Warehouse: check_inventory, create_stock_transfer, then spoken "Yes. Move it.", then confirm_stock_transfer. TR-6001 was done by voice, ERP-70001 posted, and stock moved R-12 to B-04-2 (40 to 20, 2 to 22).
  - Training: module started, three answers marked in code, finished at 50%, needs review.
- The first warehouse run failed and showed two bugs, both fixed: ASR split the yes into two finals, and the claim guard flagged "drafted" for a stock transfer.
- The ngrok tunnel flapped (restarting on blips, then "already online"); made tolerant.
- Unit tests: 73 pass. UI smoke: 0 console errors.
- Agora RESTful API key supported (`AGORA_CUSTOMER_ID` / `AGORA_CUSTOMER_SECRET`, optional). If the organisers require it, add both to `backend/.env` and restart.

## New: product page and SaaS console shell (21 Nov)
- `/` is a product page: positioning against CMMS apps and voice copilots, an animated product preview, live numbers and a one-click live demo. The console is at `/board`, with a sidebar and a KPI dashboard.
- Positioning research: CoSkip (coskip.com) is the closest product, offering voice and camera guidance from SOPs and a proof packet for field service. Shifttrace's difference is memory between shifts, the spoken-yes approval gate, writes re-read before being reported, and the claim guard.
- Verified: `tsc` and `vite build` OK. UI smoke passes with 0 console errors, including the new landing screenshot `00_landing.png`.

## New: three-panel session console (21 Nov)
- The session screen is now machine context on the left, the session trace in the centre, camera and handoff so far on the right, and a voice bar fixed at the bottom. The site navigation is cut to Shift board and Records. Dark is the default theme. One-click **Start test session** on the board.
- Verified: `tsc` and `vite build` OK. UI smoke passes with 0 console errors. `scripts/testfeed_check.py` PASS on the new layout: the agent heard the lines, read 108 °C and 7.4 mm/s off the test-feed panel, and the calls are in the audit log.

## New: test feed (21 Nov)
- You can try Shifttrace without a machine: recorded panel scenes as the camera, and recorded questions as the voice, from `demo_data/testkit.json`, played through the real Agora agent.
- Verified live with `scripts/testfeed_check.py`: the agent heard both lines, read 108 °C and 7.4 mm/s off the test-feed panel, recorded both readings as out of limit, and the calls appear in the audit log as made by the voice agent. 3 of 4 runs passed. In 1, the *Say for me* buttons never enabled although the agent had joined and spoken: they waited only on the RTC "agent joined" signal. They now also enable once the agent's first words arrive. The next run passed.

## New: one-trace console (21 Nov, second pass)
- The first redesign still read as a generic admin dashboard, and the flow was not easier. Rebuilt around a single ordered log per session, a live "Handoff so far", starting sessions without a form, and one-step hand-over. Shift-logbook look. Details in `docs/UI_DESIGN.md`.
- Verified: `tsc` and `vite build` OK. UI smoke passes, including real voice (Agora joined, camera published, agent speech and system notes interleaved in order).

## Earlier: console redesign (21 Nov)
- The console was redesigned for clarity and auditability (`docs/UI_DESIGN.md`): an HMI-style grey canvas, provenance marks, a new Audit log page with filters and an inspector, a System page, machines needing attention listed first, a tabbed session record, and handoffs as a document. Light and dark themes; works on mobile.
- `record_observation` and `update_open_item` now re-read their write like every other mutation, so the audit log shows them as Verified. 59 backend tests pass.
- Verified: `tsc` and `vite build` OK. UI smoke passes with 0 console errors in both console-only and real-voice runs (Agora joined, camera published). Screenshots are in `results/screenshots/` (01 to 15).

## New: not one use case
- **Packs** (`demo_data/packs/*`): compressor C-204 (troubleshoot), conveyor CV-310 (PM due), air handler AHU-3 (inspection round). Each pack has its own manual, parts, history, handoff, panel (`/panel/<asset>`), safety notes and reading limits.
- **Tasks** (`demo_data/tasks.json`): troubleshoot, preventive maintenance, inspection round, shift briefing (no changes). The technician picks one at session start. It sets the agent's goal, procedure, greeting and tool allowlist, which is enforced in Agora and on our server.
- **`record_reading`**: readings are checked against configured limits in code, not by the LLM.
- How to add your own: `docs/CONFIGURING_USE_CASES.md`.
- Live results on the final build: PM 13/13, inspection 10/12 (12/12 in another run), briefing 6/6, vision 24/24, approval 5/5, safety 3/3, core 16/17, everything else full marks. See `experiments/RESULTS.md`.


## Verified live (real Agora ConvoAI + Murf Falcon + MCP tools)
| Capability | Evidence |
|---|---|
| Agent start, RTC media both ways, RTM transcripts and agent state | `experiments/scenarios/*/report.md` |
| Murf Falcon `en-IN-isha` speech, recorded from the Agora audio track | `audio/*.webm`, ≈ −23 dBFS mean |
| Camera → gpt-4o-mini reads the panel (A-17 / normal / A-22), real photos, video; says "too dark" instead of inventing | vision runs |
| Full PS31 loop by voice: history → camera → technician report → open loop closed → manual §4.2 → inventory → draft → spoken "yes" → verified order → WO WAITING_PARTS | core run 16/17 |
| Next-shift briefing from stored handoff | 3/3 |
| Approval gate under adversarial phrasing | 5/5 |
| Honest failure under outage / supplier rejection / tools unreachable | failure + noise runs |
| Barge-in, typed fallback, safety (no safety certification, insists on LOTO) | pass |

## Hardened after live failures
ngrok static domain · agent-exit detection with auto-restart · Tunnel watchdog and auto-restart · start gate · per-session Agora↔tools link verification with retry · claim guard with spoken correction · filler words · deterministic visual-evidence capture · ID normalisation · think-echo isolation. 56 backend tests.

## Known weaknesses
- **Network dependence**: everything needs a stable internet link (Agora cloud ↔ laptop via ngrok). On this laptop's Wi-Fi we saw outages, a sleep, and ngrok endpoint drops. Use a reliable network or phone hotspot at the venue and keep the laptop plugged in with sleep disabled.
- The tunnel is now ngrok with a static domain (8/8 starts verified); Cloudflare quick tunnel is only a fallback.
- Latency: first audio now ~1.75 s thanks to filler words; the full answer with tool calls still takes ~5–7 s.
- Camera frames take a few seconds to reach the model at session start.
- LLM run-to-run variance remains, for example sometimes reading the panel before looking up the inspection checklist. Every miss seen on 21 Nov was safe: nothing was ordered, changed or claimed wrongly.
- About 1 in 13 agent starts still fails to reach the tools after 4 attempts. The start gate refuses, and starting again works.

## Next actions
1. Done 21 Nov: the full live suite ran end-to-end on a stable network (see RESULTS.md).
2. Rehearse `docs/DEMO_RUNBOOK.md` with a real mic and the panel on a phone; record a backup video.
