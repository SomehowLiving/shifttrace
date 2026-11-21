# Shifttrace pitch kit

Everything you need on stage: a one-liner, a 3-minute pitch with a live demo, a 60-second version, likely judge questions with answers, and a checklist. Speak the lines in quotes; *italics* are what you do on screen.

---

## The one-liner
"Shifttrace is a voice agent for frontline workers that remembers every shift and acts only on a spoken yes."

---

## The 3-minute pitch (with live demo)

### 0:00 to 0:25 The problem
"In every factory, warehouse and building, work stops and starts at shift change. The ticket system remembers *that* a machine has a problem. It doesn't remember what the last person saw, tried and ruled out. That lives in someone's head or a WhatsApp thread, so the next shift starts from zero.

And these workers can't type. Their hands are busy, they wear gloves, and the floor is loud. So we built it for voice."

*Screen: the product page, hero visible.*

### 0:25 to 0:45 What it is
"Shifttrace is a hands-free voice and camera agent, built on Agora Conversational AI with Murf Falcon as its voice. A worker walks up to a machine, starts a session, and talks."

*Click **3D floor view** in the sidebar, or scroll to "On the floor" on the product page, and let one or two steps play: the worker walks to C-204 and talks.*

"This is the idea: one worker, one machine, one voice session. Let me show you the real thing."

### 0:45 to 2:15 Live demo
*Shift board → **Open C-204** → keep "Troubleshoot a fault" and the test feed ticked → **Start session**. Wait for "Ready".*

1. **Memory.** Click *Test feed: say line* (or say it): "What happened to this compressor on the previous shift?"
   "It reads the last shift's handoff. The sensor was replaced, the alarm came back, and a bearing is suspected but not confirmed. It knows what was ruled out."
2. **Camera.** *Pick the **A-17 alarm panel** thumbnail, wait 4 seconds.* "What do you see on the panel?"
   "It reads 108 degrees, alarm A-17, and saves it as a camera observation, marked unverified. The model never claims a diagnosis."
3. **Action, with a human gate.** "Do we have the drive-end bearing? Raise a request for one."
   "Zero in stock, so it drafts the order and reads it back. Watch: nothing is ordered yet."
   *Point at the amber approval card.* Say: **"Yes, submit it."**
   "Now it's submitted. The AI can never approve its own action; only my spoken yes or a click does. And it only says 'done' after re-reading the database."
4. **Handoff.** *Click **Finish and hand over**.*
   "Every line in this handoff traces back to a record. It goes to the team's Slack, Telegram, WhatsApp or Excel, with the report attached."

### 2:15 to 2:45 Why it's more than a demo
"It isn't one use case: the same engine runs troubleshooting, preventive maintenance, inspection rounds, warehouse stock transfers, training with answers marked in code, and next-shift briefings. 22 tools over MCP.

It's built to be trusted: a spoken-approval gate, re-read verification, a claim guard that catches the agent if it says something happened that didn't, and an audit log of every tool call.

And it's built for the floor: it works with Zebra scanners. It doesn't stream all day; it pauses when nobody talks. That's about a dollar forty per worker per shift instead of fifteen."

*Optional: open **Audit log** for one second.*

### 2:45 to 3:00 Close
"We tested it against the real Agora agent, logged 44 failures, fixed every one and pinned them with 89 tests.

Shifttrace: every shift hands over, nothing gets lost. Thank you."

---

## The 60-second version (if time is short)
"At every shift change, what a technician saw, tried and ruled out gets lost. The ticket system doesn't hold it, and workers can't type with gloves on.

Shifttrace is a hands-free voice and camera agent on Agora Conversational AI with Murf Falcon. *(Demo: ask about the previous shift; it answers from the handoff. Show the alarm panel; it reads it as an unverified observation. Ask for the part; it drafts the order. Say "yes, submit it"; it submits and re-reads.)*

Nothing consequential happens without the worker's spoken yes. Every action is verified, and every line of the handoff traces to a record, which goes straight to Slack, WhatsApp or Excel. One engine covers maintenance, inspections, warehouse, training and briefings. Every shift hands over; nothing gets lost."

---

## Likely judge questions

**What exactly is Agora doing, and what did you build?**
Agora Conversational AI runs the real-time voice loop: speech recognition, the LLM turn-taking and barge-in, and Murf Falcon text-to-speech. Agora RTC carries the audio and camera, and RTM carries transcripts. We built everything behind it: the MCP tool server (22 tools), the approval gate, verification, the claim guard, the records, the integrations and the console.

**How do you stop the AI from doing something wrong?**
- Consequential actions are only drafted; they execute after the worker's own final transcript says yes after the read-back. The model cannot approve itself.
- Every write is re-read on a fresh database connection before the agent may report success.
- A claim guard flags any "I ordered" or "I checked" without a matching successful tool call.
- Each task has a tool allowlist enforced both in Agora and on our server.

**What if the AI is wrong about what it sees?**
Camera readings are stored as "camera, model reading, unverified", never as a diagnosis. A person confirms them, and the confirmation is recorded.

**Isn't a live camera and voice feed expensive at factory scale?**
It isn't live all day. The agent exists only during a session. Idle pause stops it after 3 silent minutes, the camera can be on-demand, and push-to-talk avoids false turns. At public list prices that's about $1.40 per worker per shift, versus about $14.60 if streamed all shift. A live cost meter shows the real number per session.

**How is this different from CoSkip or other voice copilots?**
They guide a worker through one job. Shifttrace remembers across shifts (open questions, what was ruled out, handoffs), gates actions on a spoken yes, verifies every write, and produces an auditable handoff that flows into the team's existing tools.

**Does it work with real devices?**
It runs in the browser on Android rugged devices, tablets and laptops. Zebra DataWedge and keyboard-wedge scanners work without integration code, the device camera can scan barcodes, and a hardware PTT button can be mapped to F9. We haven't tested on a physical Zebra device yet.

**How do you plug into a real plant?**
Verified actions become events delivered to Slack, Teams, Telegram, WhatsApp, Excel or Google Sheets, Jira, GitHub, or a signed webhook into an ERP or CMMS. A new site or machine is configuration (a "pack" of machines, manuals, limits and tasks), not code.

**How do you know it works?**
Over 20 recorded live runs against the real Agora agent, scored automatically. 44 failures were found, each with a root cause and fix, pinned by 89 tests. The Agent quality page shows the loop.

**What about privacy and safety?**
Recording is user-started and visible. Keys stay on the server. The demo data is synthetic. The agent refuses to skip lockout/tagout, and safety notes come from each machine's pack.

**What's next?**
A pilot on real rugged devices, a connector to one real CMMS, multilingual voice (Murf supports Indian languages), and supervisor analytics on recurring faults.

---

## Numbers to remember
| | |
|---|---|
| MCP tools | 22 (16 core, 6 domain) |
| Workflows | 6 (troubleshoot, PM, inspection, warehouse, training, briefing) |
| Failures logged and fixed | 44 |
| Automated tests | 89 |
| Cost per worker per shift | about $1.40 (vs about $14.60 streaming all shift) |
| Voice stack | Agora Conversational AI + Murf Falcon |

---

## Before you go on stage
1. **Wake the hosted site 2 minutes early:** open https://shifttrace.onrender.com/board and sign in. The free plan sleeps after about 15 minutes idle.
2. **Or run it locally,** which is more reliable on bad Wi-Fi: `.\start.ps1`, then http://localhost:8000. Use a phone hotspot if the venue Wi-Fi is weak.
3. **Do one warm-up session**, then start a fresh one for the judges.
4. **Use a headset** if the room is loud; the typed box is the fallback.
5. **Keep tabs open:** product page, 3D floor view, shift board, and the backup video.
6. **If anything fails:** say "Let me show you the recording" and play the backup video. Never debug on stage.
