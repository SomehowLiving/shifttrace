# Commudle submission: copy-paste text

## Title
Shifttrace: Voice AI for the Shift Handover

## Description

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

**Covers the whole Voice AI at Work track**
- Field technician troubleshooting
- Factory floor preventive maintenance
- Facilities inspection rounds
- Warehouse and logistics: stock transfers, shipments, barcode scans
- Training and onboarding, with answers marked in code, not by the model
- Read-only shift briefings

Each use case is configuration (packs and tasks), not new code.

**Built with**
- **Agora Conversational AI Engine** for real-time voice, with the agent's tools served over MCP, and Agora RTC/RTM for audio, camera and transcripts
- **Murf Falcon** text-to-speech for the agent's voice
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

## Images (upload in this order; the first is the thumbnail)
1. `00-cover.png`: cover / thumbnail
2. `10-architecture.png`: architecture mind map (seven layers, 22 MCP tools, one voice turn end to end)
3. `02-floor-3d-walk.png`: 3D view, worker walks to the compressor
4. `03-floor-3d-spoken-approval.png`: 3D view, order drafted, waits for a spoken yes
5. `06-live-session-trace.png`: live session trace (camera evidence, hypotheses, handoff so far)
6. `05-shift-board.png`: shift board
7. `07-handoff.png`: shift handoff report
8. `04-floor-3d-handoff.png`: 3D view, handoff sent to the team's tools
9. `08-connected-systems.png`: connected systems
10. `09-agent-quality.png`: agent quality and improvement loop

All are 1920 x 1080 PNG.

## Tags (press Enter after each)
voice-ai, agora, conversational-ai, murf-ai, frontline-workers, industrial-ai, maintenance, mcp, ai-agents, react, fastapi, hackathon
