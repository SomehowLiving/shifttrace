# Shifttrace pitch kit

Everything you need on stage, checked against the PS31 brief ("Voice AI at Work: Beyond the Call Center"):
- how Shifttrace meets each requirement;
- a 3-minute pitch and live demo that walks the required five-stage flow by name;
- a 60-second version;
- answers to the judges' likely questions, including the honest gaps;
- a checklist.

Speak the lines in quotes. *Italics* are what you do on screen.

---

## The one-liner
"Shifttrace is a voice agent for frontline workers that remembers every shift and acts only on a spoken yes."

---

## Does Shifttrace meet the brief? Yes, requirement by requirement

| PS31 asks for | Shifttrace | Where to show it |
|---|---|---|
| **Voice-first, agentic workplace assistant** | Hands-free voice and camera agent; workers talk, it acts through tools | Any live session |
| **Agora Conversational AI** | Runs the voice loop: speech recognition (Deepgram nova-3), LLM turns (gpt-4o-mini with vision), barge-in | Session; System page shows the pipeline |
| **Agora RTC and/or Chat** | Agora RTC for audio and camera, Agora RTM (Signaling) for live transcripts and agent state. Agora Chat is not used; the brief says "and/or" | Session, Voice pipeline panel |
| **Murf AI Falcon TTS** | The agent's only voice (never browser speech) | Session |
| **LLMs, RAG, tool calling, MCP** | 22 tools served to Agora over MCP. Retrieval from the machine manual (BM25), records, history and the last handoff | Architecture slide; audit log |
| **Enterprise knowledge + context** | Machine history, open work orders, the previous shift's handoff, manuals and SOPs, stock by location | "What happened last shift?" |
| **Meaningful actions across connected systems** | Orders, stock transfers with ERP postings, work-order updates, escalations, follow-ups, learning records. Events go out to Slack, Teams, Telegram, WhatsApp, Excel/Sheets, Jira, GitHub and webhooks | Order demo; Connected systems page |
| **Confirmation for critical actions** | Drafted, read back, and executed only on the worker's spoken yes (or a console click). The AI cannot approve itself | Approval card, "Yes, submit it" |
| **Handles errors** | Says plainly when something failed or wasn't changed. Failure switches: stock system outage, supplier rejects order. Claim guard catches false "done" | System page failure switches |
| **Follow up: update systems, summary, follow-ups** | Shift handoff from records (HTML + Excel), follow-ups with calendar links, events to the team's tools, next-shift voice briefing | Finish and hand over |
| **At least one complete end-to-end workflow** | Six: field technician troubleshooting, factory PM, facilities inspection, warehouse and logistics, training and onboarding, read-only shift briefing | Shift board → any machine |
| **Measurable improvements** | Cost per worker shift (live meter), agent quality across 20 live runs, latency, and the handoff written automatically. See the efficiency question below | Agent quality page; cost chip |
| **Innovative beyond the examples** | Memory between shifts (the handoff as a first-class record), spoken-yes gate, re-read verification, provenance on camera readings, 3D floor view | Pitch close |

### The five required demo stages, as you'll show them
| Stage | In the C-204 demo |
|---|---|
| **1. Initiate** | Worker starts a voice session and asks, "What happened to this compressor on the previous shift?" (Agora Conversational AI, Murf Falcon voice) |
| **2. Understand** | Agent reads the previous handoff, open questions and work orders; reads the A-17 alarm through the camera; finds manual section 4.2 |
| **3. Execute** | `check_inventory` (0 in stock) → `create_procurement_request` (draft PR-2001) → `update_work_order` |
| **4. Confirm** | Reads the order back and waits. Worker says "Yes, submit it." Submitted, then re-read from the database before it says "done". If the supplier rejects it, it says so |
| **5. Follow up** | Shift handoff written from records, sent to Slack / Telegram / Excel with the report attached; follow-up scheduled; next shift hears it by voice |

---

## The 3-minute pitch (with live demo)

### 0:00 to 0:25 The problem
"The brief asks how voice AI can help people get work done hands-free. Here's where it matters most: shift change. The ticket system remembers *that* a machine has a problem. It doesn't remember what the last person saw, tried and ruled out. That lives in someone's head or a WhatsApp thread, so the next shift starts from zero. And these workers can't type: gloves, noise, hands full."

*Screen: product page.*

### 0:25 to 0:40 What it is
"Shifttrace is a hands-free voice and camera agent on Agora Conversational AI, with Murf Falcon as its voice and 22 tools over MCP."

*Show the architecture slide or the 3D floor view for a few seconds.*

### 0:40 to 2:15 Live demo: the five stages
*Shift board → **Open C-204** → "Troubleshoot a fault", test feed on → **Start session**. Wait for "Ready".*

1. **Initiate.** "What happened to this compressor on the previous shift?"
   "I'm just talking. Agora handles the conversation and Murf is the voice."
2. **Understand.** "It pulled the last shift's handoff: sensor replaced, alarm came back, bearing suspected but not confirmed."
   *Pick the **A-17 alarm panel**, wait 4 seconds.* "What do you see on the panel?"
   "It reads 108 degrees, alarm A-17, and saves that as an unverified camera observation, not a diagnosis."
3. **Execute.** "Do we have the drive-end bearing? Raise a request for one."
   "It checked stock (zero) and drafted the order."
4. **Confirm.** *Point at the amber card.* "Critical actions need a human. It reads the order back and waits." Say **"Yes, submit it."**
   "Now it's submitted, and it re-read the database before saying so. If the supplier had rejected it, it would tell me plainly."
5. **Follow up.** *Click **Finish and hand over**.*
   "The service report writes itself from records. It's sent to the team's Slack, Telegram or Excel with the report attached, a follow-up is scheduled, and the next shift can ask for it by voice."

### 2:15 to 2:45 Beyond one workflow
"This isn't one demo. The same engine runs every example in the brief: field technician, factory floor, warehouse with stock transfers and ERP postings, training with answers marked in code, and productivity with follow-ups and calendar links.

It's built to be trusted: a spoken-yes gate, re-read verification, a claim guard and a full audit log. It's built for the floor: Zebra scanners, push-to-talk, and it pauses when nobody talks. That's about a dollar forty per worker per shift instead of fifteen."

### 2:45 to 3:00 Close
"We ran it 20 times against the real Agora agent and logged 44 failures. Every one was fixed and pinned with a test, 89 tests in all. Shifttrace: every shift hands over, nothing gets lost."

---

## The 60-second version
"At every shift change, what a technician saw, tried and ruled out gets lost, and workers can't type with gloves on. Shifttrace is a hands-free voice and camera agent on Agora Conversational AI with Murf Falcon.

*(Demo: ask about the previous shift; it answers from the handoff. Show the alarm panel; it reads it as an unverified observation. Ask for the part; it checks stock and drafts the order. Say "yes, submit it"; it submits and re-reads. Finish; the handoff goes to Slack and Excel.)*

That's initiate, understand, execute, confirm and follow up, with nothing critical happening without a spoken yes. One engine covers maintenance, inspections, warehouse, training and briefings. Every shift hands over; nothing gets lost."

---

## Judges' questions, answered

### About the brief

**Which part of the problem statement does this solve?**
The core question: getting information, resolving issues and completing workflows hands-free. It covers all five example solutions on one engine, with the field-technician flow (Before, During, Action, After) as the main demo.

**Show me the full Before / During / Action / After flow.**
- **Before:** it retrieves the work orders, equipment history and the last shift's handoff.
- **During:** voice troubleshooting with the camera and the manual.
- **Action:** stock check, draft order, spoken yes, work-order update, escalation if needed.
- **After:** handoff report (HTML and Excel), records updated, follow-ups scheduled, events sent to the team's tools.

**Where is the RAG?**
Retrieval from enterprise knowledge before every answer: the machine manual and SOPs (BM25 search, the agent cites section numbers), equipment history, open questions, stock and the previous handoff. It is retrieval through tools rather than a vector database. That keeps answers traceable to a record, which matters for an auditable handoff.

**Do you use Agora Chat?**
No. We use Agora Conversational AI, Agora RTC (audio and camera) and Agora RTM/Signaling (live transcripts and agent state). The brief asks for RTC *and/or* Chat.

**How exactly is Murf Falcon used?**
It is the TTS module inside Agora Conversational AI, bring-your-own-key. Every word the agent speaks is Murf Falcon. We deliberately did not use Agora's speech-to-speech mode, because it would bypass Murf.

**What are the "connected systems"? Are they real?**
- **Real connectors:** Slack, Microsoft Teams, Telegram, WhatsApp Cloud API, Excel (Power Automate) / Google Sheets, Jira, GitHub, and HMAC-signed webhooks. Each turns on when its keys are added; deliveries are logged and retried. They are tested with mocked transports and a local signed-webhook receiver, not yet against live accounts.
- **Simulated:** the CMMS, stores and ERP are built in with synthetic data, so the demo runs anywhere. A real plant would connect through the webhook or an API adapter.

**How does it handle errors?**
- It never claims success without re-reading the database.
- If a tool fails, it says so and that nothing changed. You can show the "stock system outage" and "supplier rejects orders" switches on the System page.
- If it claims an action without a matching successful tool call, the claim guard flags it and makes it correct itself.

**Where's the confirmation for critical actions?**
Orders and stock transfers are drafted, read back, and only executed when the worker's own final transcript says yes after the read-back, or someone clicks approve. "Yes. … No, wait." does not approve. The model has no way to approve on its own.

**What measurable improvement does it deliver?**
What we measured:
- **Cost per worker shift:** about $1.40 at list prices with idle pause, versus about $14.60 if streamed all shift. A live meter shows it per session.
- **Agent reliability:** 20 scored live runs against the real Agora agent. The first run passed 35% of checks; later full runs reached 100%.
- **Speed:** first audio in about 1.75 seconds; a full answer with tool calls in 5 to 7 seconds.

What it removes: the handoff report and the system updates are written automatically from records. No typing at the machine, and no searching chat threads at shift start.

We have not run a time-and-motion study with real technicians. That's the first thing a pilot would measure: time to resume work at shift start, and repeat faults.

**What is innovative beyond the examples?**
- Memory between shifts: the handoff is a first-class record the next shift can question by voice.
- A spoken-yes gate tied to the transcript order.
- Verification and a claim guard, so the agent can't say "done" when it isn't.
- Camera readings carry their provenance.
- Cost controls for the factory floor.

### About the product

**How do you stop the AI from doing something wrong?**
- **Approval:** consequential actions need the worker's spoken yes.
- **Verification:** every write is re-read before the agent reports success.
- **Claim guard:** catches false "done" claims.
- **Allowlists:** per-task tool lists, enforced both in Agora and on our server. A read-only briefing physically can't place an order.

**What if the AI misreads the camera?**
Camera readings are stored as "camera, model reading, unverified" and are never presented as a diagnosis. A person confirms them, and that confirmation is recorded.

**Isn't always-on voice and video too expensive for a factory?**
It isn't always on:
- The agent exists only during a session.
- Idle pause stops it after 3 silent minutes.
- The camera can be on-demand.
- Push-to-talk avoids false turns.

The result is about $1.40 per worker per shift, versus about $14.60 if streamed all day.

**How is this different from CoSkip or other voice copilots?**
They guide one job. Shifttrace remembers across shifts, gates actions on a spoken yes, verifies every write, and hands over an auditable record into the team's existing tools.

**Does it work on real devices?**
It runs in the browser on Android rugged devices, tablets and laptops. Zebra DataWedge and keyboard-wedge scanners work with no integration code, the camera can scan barcodes, and a PTT button can map to F9. We haven't tested on a physical Zebra device yet.

**How would a new site adopt it?**
A site is configuration: a "pack" with its machines, manuals, limits, safety notes and tasks. Then add the connector keys (Slack, ERP webhook and so on). No code changes.

**Is it multilingual?**
The voice stack supports it (Murf Falcon has Indian-language voices), but the demo is English. Hindi and regional languages are next.

**Privacy and safety?**
- Recording is started by the user and visibly shown.
- API keys stay on the server.
- The hosted console is password-protected.
- Demo data is synthetic.
- The agent refuses unsafe requests such as skipping lockout/tagout.

**What's next?**
A pilot on rugged devices, a live CMMS/ERP connector, multilingual voice, and supervisor analytics on repeat faults.

### Honest gaps (say these before they're found)
- The CMMS, stores and ERP are simulated with synthetic data. The outbound connectors are real but not yet tested against live accounts.
- No measured productivity study with real workers yet.
- Meeting management (from the Productivity example) is limited to follow-ups and calendar links.
- Not yet tested on a physical Zebra device.

---

## Numbers to remember
| | |
|---|---|
| MCP tools | 22 (16 core, 6 domain) |
| Workflows | 6 (troubleshoot, PM, inspection, warehouse, training, briefing) |
| Live runs vs the real Agora agent | 20 scored |
| Failures logged and fixed | 44 |
| Automated tests | 89 |
| First audio / full answer with tools | about 1.75 s / 5 to 7 s |
| Cost per worker per shift | about $1.40 (vs about $14.60 streaming all shift) |
| Voice stack | Agora Conversational AI + RTC + RTM, Murf Falcon |

---

## Before you go on stage
1. **Wake the hosted site early.** Open https://shifttrace.onrender.com/board 2 minutes before and sign in; the free plan sleeps after about 15 minutes idle.
2. **Or run it locally,** which is more reliable on bad Wi-Fi: `.\start.ps1`, then http://localhost:8000. Use a phone hotspot if the venue Wi-Fi is weak.
3. **Warm up,** then start a fresh session for the judges.
4. **Use a headset** if the room is loud. The typed box is the fallback.
5. **Keep tabs open:** product page, architecture image, 3D floor view, shift board, backup video.
6. **If anything fails,** play the backup video. Never debug on stage.
