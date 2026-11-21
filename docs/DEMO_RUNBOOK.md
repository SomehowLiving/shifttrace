# Demo runbook (target 3:00)

## Before judges arrive
1. `.\start.ps1 -Reset`, wait for `tunnel MCP self-test: PASS`.
2. `cd backend; uv run python -m app.preflight`: all OK.
3. Open http://localhost:8000 in Edge or Chrome on the laptop. Open http://localhost:8000/panel/C-204 on a second screen or phone, with TEMP HIGH lit and A-17 / 108 °C / 7.4 mm/s showing.
4. Headset recommended (venue noise). Typed fallback box exists on the live screen.
5. Do one 30-second warm-up session, then **Reset demo data** (**System** in the header).

## No machine? Use the test feed
1. Open http://localhost:8000 (the product page) and click **Try the live demo**, or click **Start test session** on the Shift board (`/board`). For another machine, use **Open CV-310** or **Open AHU-3**, keep *Use the test feed* ticked and click **Start session**. Allow the microphone if you want to talk too; it is optional.
2. The camera panel on the right shows the machine's panel. The thumbnails under it switch scenes: the alarm panel, a normal panel, a real panel video, gauges, or a covered camera.
3. When the bottom bar says *Ready*, click the violet **Test feed: say line 1 of N** button. Each click plays the next line as your voice, and the arrow beside it lists every line. Lines that need the camera switch to the right panel first and hold it for about 4 seconds.
4. Watch **This session, in order** and **Handoff so far** fill in. Approve the order when the card appears (say line 8, or click **Approve & submit**). Then click **Finish and hand over**.
5. Open **Audit log** (in the session header, or in the nav filtered to the session) and click any row to see exactly what the agent sent and what came back.

Also try the safety and edge lines: *Can I skip the lockout?* (it must refuse), *No, wait. Don't submit it yet.* (nothing is ordered), and the cricket question (it steers back).

## Script
**0:00 Hook (spoken by presenter).** "Every machine has a ticket history. What gets lost at shift change is what people saw, tried and ruled out. SHIFTTRACE keeps that."

**0:15 Before.** Shift board: C-204 shows the 3 questions Anil's shift left open. **Open C-204**: point at *Still open* and the struck-through "Sensor TS-2" hypothesis in the log. Check the header says *On shift Kavya Rao, A shift*, keep *Troubleshoot a fault*, and click **Start session**.
- Say: "What happened to this compressor on the previous shift?"
- Expect: a "Read the previous handoff" line on the trace; the agent says the sensor was replaced, A-17 came back, DE vibration 7.4, bearing suspected not confirmed, coupling unchecked.

**0:45 During.** Point the camera at the panel and **hold it steady for ~5 seconds before asking** (measured: frames reach the model with a lag).
- Say: "I'm looking at the panel now. What do you see?"
- Expect: it reads TEMP HIGH / A-17 / 108 °C; a **Camera, model reading** evidence item (outline diamond, *Unverified*) appears on the trace and under *Seen and said* in *Handoff so far*, with the frame attached.
- Say: "It shook first, then the warning came on."
- Expect: technician statement recorded; the agent offers to close the open question "before or after" (`update_open_item`).
- Optional: "What does the manual say about A-17 coming back after a sensor swap?" → manual section 4.2.

**1:30 Action.** "Do we have the drive-end bearing?"
- Expect: `check_inventory` → BRG-6316-C3, 0 available.
- "Raise a request for one and put the work order on hold for parts."
- Expect: an ochre **Approval required** card pins under the trace; the agent reads it back and asks.
- Say: "Yes, submit it."
- Expect: `approve_procurement_request` ok, "PR-2001 submitted to supplier" appears on the trace as a verified change (open *detail* for the spoken approval quote), and *Handoff so far* moves it to *Done and verified*. Then `update_work_order` → WAITING_PARTS.

**2:15 After.** Point at *Handoff so far*, then click **Finish and hand over**: the handoff sheet opens. At the bottom, **Hand over C-204** to Dev Malhotra, B shift → **Start next-shift briefing**.
- Say: "What happened with C-204, what did we try, and what's still open?"
- Expect: the answer comes from H-0043: bearing ordered with ETA, camera observation labelled as such, vibration-before-warning answered, coupling still open.

**2:50 Close.** Back on the handoff sheet (still open first; every line maps to a record), open **Audit log for this session**: each change shows *Verified* because it was re-read from the database. "Real Agora voice, Murf Falcon, real tool calls and state changes; the plant data is synthetic."

## Failure demos (if asked)
- System → *Stock system outage* → ask about the bearing: the agent must say stock is unknown and that nothing changed (tool call shows red).
- System → *Supplier rejects orders* → approve: the card shows *Rejected* with the reason; the agent must not say "ordered".
- Say "submit it" **before** the read-back: the approval tool returns APPROVAL_REQUIRED (shown as *Needs approval* in tool calls and the audit log).

## Recovery
- Agent silent: check the agent state next to the camera (open *Voice pipeline* for the audio and message connection) and the issue banner. End the session and start again (≈5 s).
- Tunnel dead: restart `start.ps1` (new URL; sessions pick it up automatically).
- Everything down: show `results/screenshots/` and the backup recording.

## Beyond maintenance (60 s each, test feed works for both)
- **Warehouse and logistics:** Shift board → **Open DC2-ZB** → *Warehouse operations* → Start. Say or play: "How much basmati rice do we have, and where is it?", then "Move twenty cases ... from reserve R twelve to the pick face B zero four two." It reads the transfer back and an ochre confirmation card appears. Say "Yes, move it." The trace shows *TR-6001 done … ERP ERP-70001*, and **Stock, orders, follow-ups** shows the new quantities. Also: "Where is the rice delivery?" (tracking) and "Schedule a follow-up for the next shift to recount the oil" (follow-up).
- **Training and onboarding:** **Open C-204** → *Training and onboarding* → Start. "Train me on the safety basics", then answer three questions; the test feed plays one correct, one partly and one wrong answer. Finish: the score is 50%, recorded as *needs review*, and the agent offers a retraining follow-up. Point out that the marking is done in code against the manual; the model is never given the answer key.

## Real integrations and the improvement loop (60 s)
- **Connected systems:** with Slack, Teams, Jira, GitHub or a webhook configured in `backend/.env`, every verified action is delivered there; for example, an escalation becomes a Slack message and a Jira issue. Without accounts, turn on **Local test receiver**: each order, transfer, follow-up or handoff from a session appears in the event log as "delivered, signature valid". **Follow-ups calendar (.ics)** opens in Google Calendar or Outlook.
- **Agent quality:** the chart shows the pass rate rising from 35% on the first live run to the mid-90s. **Failures and fixes** lists the 41 problems found, each with its root cause and fix. **Dataset** shows the Creative Commons photos and videos the agent is tested on.

## Showing it is not a one-off script (optional, 60 s)
The same agent handles other machines and other jobs, driven by configuration (`docs/CONFIGURING_USE_CASES.md`):
- **Preventive maintenance on conveyor CV-310** (show `/panel/CV-310`). Start session, task *Preventive maintenance*. Say "Okay, start the checklist." The agent reads step 1, the lockout. Ask to skip it and it refuses. Report each step and it records each one.
- **Inspection round on AHU-3** (show `/panel/AHU-3`). Task *Inspection round*. Say "Read the filter pressure off the display." It reads 262 Pa, says that is above the 250 Pa change limit (section 3.1), and logs it for follow-up.
- **Shift briefing (no changes)**. Ask "order the gear oil" and the agent says it is not available in a briefing session. The tool is not even offered to it, and the server would reject it anyway.

