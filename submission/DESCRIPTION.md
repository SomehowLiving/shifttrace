**Every shift hands over. Nothing gets lost.**

Frontline teams lose knowledge at every shift change. What a technician saw, tried and ruled out ends up in their head or a chat thread, so the next shift starts over. Shifttrace is a hands-free voice and camera agent for frontline workers that remembers every shift and only acts on a spoken yes.

**How it works**
A worker starts a voice session at a machine and talks naturally, with a headset or a rugged handheld.
- The agent recalls the previous shift's handoff, open questions and work orders.
- It reads the machine panel through the live camera. Readings are saved as model observations, never as a confirmed diagnosis.
- It looks up the manual, stock and history through 22 tools over MCP.
- It drafts consequential actions (a part order, a stock transfer) and reads them back. Nothing happens until the worker says yes out loud. The AI can never approve its own action.
- Every change is re-read from the database before the agent may say it is done. A claim guard catches the agent if it says something happened that did not.
- At the end it writes a shift handoff where every line traces to a record. The handoff goes to the team's Slack, Teams, Telegram, WhatsApp, Excel or calendar, with the report attached.

**Architecture: seven layers**
1. Device: a browser on a phone, laptop or rugged handheld, with mic, camera, push-to-talk and a barcode scanner.
2. Real-time voice: Agora RTC carries audio and video, and Agora RTM carries transcripts and agent state. The Agora Conversational AI Engine runs speech recognition (Deepgram nova-3, managed), a vision-capable LLM (gpt-4o-mini, managed) and Murf Falcon text-to-speech.
3. Tools: the Shifttrace MCP server (FastMCP, streamable HTTP). It is the only port exposed to the internet, and Agora must present a bearer token to call it.
4. Trust: a spoken-approval gate, a re-read before anything is reported as done, a claim guard, and provenance on every record.
5. Records: SQLite as the system of record, an audit log of every tool call, and site "packs" (JSON configuration for machines, manuals, limits and tasks).
6. Integrations: Slack, Microsoft Teams, Telegram, WhatsApp, Excel / Google Sheets, Jira, GitHub, signed webhooks, and calendar links.
7. Console: a React app with the shift board, live session trace, handoff, audit log, records, agent quality page and a 3D floor view.

**The 22 MCP tools**
The agent can act only through these tools. Each task has its own allowlist, enforced twice: in Agora's allowed tools and again on the server. A read-only briefing cannot reach a write tool, even if the model tries.

Core tools (16), available in every task:
- get_asset_history: the machine's memory, with work orders, their log and recent technician entries
- get_previous_handoff: the last shift's handoff, with what was seen, what was verified and what was left open
- get_open_items: hypotheses and questions that no shift has closed yet
- get_open_work_orders: open work orders with status, priority and notes
- search_maintenance_manual: searches the machine's manual (BM25); the agent quotes the section number
- check_inventory: stock by part, with quantity, location, lead time and open orders
- reserve_spare_part: reserves an in-stock part against a work order
- create_procurement_request: drafts an order for an out-of-stock part; nothing is ordered yet
- approve_procurement_request: submits the order, only after the worker's spoken yes
- update_work_order: adds a note and changes the status
- escalate_incident: raises an escalation to the supervisor with a severity and a reason
- record_observation: saves what was seen or suspected, tagged with its source
- record_reading: saves a numeric reading and checks it against the machine's limits
- update_open_item: closes a hypothesis or question as confirmed, ruled out or answered, with the evidence
- create_shift_handoff: writes the handoff from stored records only
- schedule_follow_up: schedules what, when and who, from spoken due dates

Domain tools (6), switched on per task:
- track_shipment: carrier status, last scan, ETA and items on board
- create_stock_transfer: drafts a stock move between locations
- confirm_stock_transfer: moves the stock and posts it to the ERP, only after a spoken yes
- get_training_module: starts a training module, with its questions and pass mark
- record_training_answer: marks a spoken answer in code against the manual (the model never sees the answer key)
- finish_training_module: scores the module and updates the learning record

**One order, step by step**
get_previous_handoff → record_observation (camera: "A-17 DISCH TEMP HIGH, 108 °C") → search_maintenance_manual ("A-17") → check_inventory (0 in stock) → create_procurement_request (draft PR-2001, read back) → the worker says "Yes, order it." → approve_procurement_request (checked against the transcript, submitted, re-read) → event sent to Slack, Telegram and Excel → create_shift_handoff.

**Covers the whole Voice AI at Work track**
- Field technician troubleshooting
- Factory floor preventive maintenance
- Facilities inspection rounds
- Warehouse and logistics: stock transfers, shipments, barcode scans
- Training and onboarding, with answers marked in code, not by the model
- Read-only shift briefings

Each use case is configuration (packs and tasks), not new code.

**Built with**
- Agora Conversational AI Engine for real-time voice, with the agent's tools served over MCP, and Agora RTC/RTM for audio, camera and transcripts
- Murf Falcon text-to-speech for the agent's voice
- A vision-capable LLM for reading the camera
- FastAPI, SQLite, React and three.js

**Built for the floor, priced for it**
- Idle pause, camera on demand and push-to-talk mean nothing streams all day.
- A live cost meter shows the cost per session and per shift.
- Works with Zebra DataWedge and keyboard-wedge barcode scanners, or the device camera.

**Proof, not slides**
- 44 failures found in live runs against the real Agora agent are logged with their root cause and fix.
- 89 automated tests pin those fixes.
- An Agent quality page shows the improvement loop.

All demo data is synthetic.
