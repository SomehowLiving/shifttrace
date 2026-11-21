# SHIFTTRACE — Project Context, PS31 Brief and Product Strategy

**Prepared:** 19 November 2026  
**Event:** Build with Agora — Bengaluru 2026  
**Selected problem statement:** `ps31` — Voice AI at Work: Beyond the Call Center / Field Technician Copilot workflow  
**Working project name:** SHIFTTRACE  
**Status:** Concept and hackathon plan; not yet a verified working product

---

## 1. Executive brief

SHIFTTRACE is a voice-first, multimodal maintenance continuity assistant for industrial teams.

Its central idea is:

> **The maintenance system remembers the tickets. SHIFTTRACE remembers what actually happened.**

A conventional maintenance workflow records structured outcomes: a ticket was opened, a part was replaced, an inspection was performed, a work order was closed. Important context often remains scattered across technician conversations, photographs, observations, sounds, failed attempts and people's memories.

SHIFTTRACE helps preserve that context across a maintenance session and across shift handovers. A technician can speak naturally, show the equipment through a phone camera, retrieve equipment history and manuals, ask for inventory checks, update a work order and create an evidence-backed handoff for the next shift.

The product is not meant to autonomously diagnose dangerous machinery or replace an authorised technician. AI observations are presented with their source and uncertainty. Safety-critical work remains under human control.

### One-sentence pitch

**SHIFTTRACE gives every machine an evidence-backed operational memory, so each technician can understand what happened, act on it and hand over the complete context to the next shift.**

### Why this direction

The project connects three interests that have been developed in the preceding research:

1. **Multimodal perception:** MiniCPM-o 4.5 inspired the exploration because its demo combines continuous audio/video input, temporal observations and spoken responses.
2. **Real-time interaction:** Agora Conversational AI, Agora RTC and Murf Falcon provide the required live voice interface and speech output for the hackathon.
3. **Agentic execution:** A backend can retrieve maintenance records, check inventory, update a work order and generate a handoff through real APIs.

The important distinction is that the multimodal model is not the product by itself. It is one part of a working workplace workflow.

---

## 2. Hackathon context — Build with Agora, Bengaluru 2026

### Event facts

- **Date:** Saturday, 21 November 2026.
- **Time:** 8:30 AM–6:30 PM IST.
- **Venue:** Polaris School of Technology, DivyaSree Technopark, A3, EPIP Zone, Brookefield, Bengaluru, Karnataka 560066, India.
- **Format:** Solo hackathon; in-person final day, with remote building and mentorship beforehand.
- **Organiser:** KNOTiC.
- **Powered by:** Agora.
- **Exclusive partner:** Murf AI.
- **Technology partner:** AWS.
- **Platform partner:** Commudle.
- **Learning partner:** Packt.
- **Published prize package:** $3,000 total package, consisting of $2,000 cash plus gadgets. The published cash prizes are $1,000 for the winner, $600 for first runner-up and $400 for second runner-up; gadgets include one PS5, five wireless earbuds and two mechanical keyboards.

Official event pages:

- Event: https://buildwithagora.knotic.co/
- Luma: https://luma.com/2g5vcgrr?tk=8AXBfg
- Commudle overview: https://www.commudle.com/communities/knotic/hackathons/build-with-agora-blr
- Commudle tracks: https://www.commudle.com/communities/knotic/hackathons/build-with-agora-blr/tracks
- Official Agora Discord: https://discord.gg/9Vg3Qafc7
- Official participant WhatsApp group: https://chat.whatsapp.com/DiKHDmxyyZ15SyoaaGK0fD?mode=gi_t

**Important date note:** The official KNOTiC agenda says shortlisted participants must confirm their participation and track by 19 November 2026 at 5:00 PM IST. Commudle may display different registration metadata. Treat the organiser's earlier 5 PM deadline as the safe operational deadline and check the participant portal directly.

### Stated common technology expectation

The official event page says the project should use:

- Agora Conversational AI for real-time voice.
- Murf AI Falcon TTS for voice output.
- Agentic AI that calls tools and APIs to get things done.

Agora RTC and/or Agora Chat may be used as supporting real-time infrastructure. The project may use other models and services for perception, reasoning, retrieval or specialised tasks, but those do not replace the required Agora and Murf usage.

### Judging rubric supplied by the participant

The participant shared the following five criteria:

1. Problem-solution fit.
2. Innovation.
3. Use of Agora Voice AI.
4. Product functionality.
5. Future scope of scalability and real-world use case.

The public organiser site says detailed judging criteria will be shared with shortlisted participants and covered at the opening. It does not publish percentage weightings. Do not invent weights.

### Selected track and exact PS31 brief

**Track:** Voice AI at Work: Beyond the Call Center  
**Problem statement ID:** `ps31`  
**Theme:** From Workplace Assistance to Intelligent Action

The official problem asks how real-time voice AI can improve workplace productivity by helping employees access information, resolve issues, automate repetitive tasks and complete business workflows through natural, hands-free conversations.

It asks participants to build a voice-first, agentic workplace assistant combining enterprise knowledge, contextual intelligence and tool calling across connected systems.

The published Field Technician Copilot example describes:

- **Before:** Retrieve assigned tickets, equipment history and maintenance records.
- **During:** Diagnose issues through interactive voice troubleshooting.
- **Action:** Check spare-part availability, raise orders, update tickets or escalate incidents through APIs.
- **After:** Generate service reports, update records and initiate follow-ups.

Technology focus:

- Agora Conversational AI.
- Agora RTC and/or Agora Chat.
- Murf AI Falcon TTS.
- LLMs and RAG.
- Tool calling.
- MCP-compatible integrations.
- Enterprise APIs.

Required demo flow:

1. **Initiate:** Employee interacts through natural voice using Agora Conversational AI and Murf Falcon TTS.
2. **Understand:** AI interprets the request, retrieves relevant enterprise information and identifies the action.
3. **Execute:** AI uses tools or external APIs to perform meaningful actions such as updating tickets, checking inventory or scheduling tasks.
4. **Confirm:** AI communicates the outcome, handles errors and seeks user confirmation for critical actions.
5. **Follow up:** AI updates systems, generates summaries or initiates follow-up activities.

Expected deliverable: a working voice AI assistant demonstrating natural conversations, enterprise knowledge integration and at least one complete workplace workflow with meaningful actions across connected systems.

The track explicitly encourages innovative workplace use cases beyond the example, especially intelligent automation, multi-step workflows and measurable operational efficiency.

---

## 3. Product idea: machine memory, not another maintenance chatbot

### The underlying observation

A machine's history is not just a list of service tickets. During a real maintenance session, a technician may:

- Hear an unusual sound.
- Notice a warning light.
- Observe a changing reading.
- Explain what they expected to happen.
- Try a procedure.
- Make an adjustment.
- Discover that the symptom persists.
- Ask for a part or escalation.

The structured ticket may record only a small portion of this context. The next shift may not know what was seen, heard, tried, ruled out or left unresolved.

### SHIFTTRACE proposition

Create a timestamped, source-attributed operational timeline for each asset and maintenance session. Combine it with equipment history, work orders, manuals and inventory. Allow technicians to use natural voice to query the timeline and perform approved actions.

### Four product stages

#### A. Machine Memory — Before the session

A technician scans an equipment QR code or selects an asset. SHIFTTRACE retrieves:

- Asset identity, model and known metadata.
- Active work orders.
- Previous maintenance sessions.
- Previous observations and technician statements.
- Parts replaced or requested.
- Pending actions and unresolved questions.
- Relevant manual sections and procedures.

Example question: “What happened to compressor C-204 on the previous shift?”

#### B. Live Observation — During the session

The technician starts an explicitly indicated session and uses a phone camera and microphone. The system can:

- Interpret visible indicators, labels and displays.
- Capture technician statements and explanations.
- Associate observations with timestamps.
- Optionally classify salient audio events.
- Retrieve relevant historical evidence.
- Ask clarifying questions.

The system must distinguish what was visibly observed, what the technician stated, what a business record confirms and what the model inferred.

#### C. Agentic Execution — Action

The agent can:

- Search the maintenance manual.
- Retrieve asset history.
- Check part inventory.
- Prepare a spare-part reservation or procurement request.
- Update a work order.
- Escalate to a supervisor.
- Generate a report.

Consequential actions require explicit technician confirmation. Each action must be verified against the result returned by the backend.

#### D. Operational Continuity — After the session

Generate a shift handoff containing:

- Reported issue.
- Observed evidence.
- Technician statements.
- Historical records consulted.
- Procedures attempted.
- Actions actually completed.
- Actions that failed.
- Parts requested or unavailable.
- Current status.
- Unresolved questions.
- Suggested next steps, clearly labelled as suggestions.

The next technician can query the handoff and navigate back to its supporting evidence.

---

## 4. Differentiation and novelty

Do not claim that SHIFTTRACE is the first maintenance-memory or AI maintenance product. Existing CMMS and industrial AI products already cover parts of this territory.

The proposed differentiation for this hackathon is the combination of:

1. **Live multimodal evidence:** Audio/video observations are captured during the maintenance workflow, not only in an after-the-fact report.
2. **Operational memory across shifts:** Session context is structured and made retrievable for the next technician.
3. **Evidence provenance:** The system separates model observations, technician statements, authoritative records and AI inferences.
4. **Voice-first action:** The technician can retrieve, update and request actions without constantly switching to forms or menus.
5. **Verifiable execution:** The agent checks whether work-order and inventory actions actually succeeded before claiming completion.

The distinctive product promise is continuity of operational context, not “AI diagnoses a machine.”

### What makes a hackathon idea strong

Use the following ideation discipline. It reflects the approach we want for this project: solve the selected problem faithfully while finding a less-obvious angle and making the result tangible.

#### 1. Start from the human workflow, not the technology

Map what the worker is trying to accomplish before choosing models or APIs. Identify handoffs, context loss, repeated explanations, delays and places where people must stop work to enter information.

#### 2. Separate the stated problem from the organiser's example

PS31 is mandatory. “Field Technician Copilot” is an example workflow, not a requirement to copy the example's exact implementation. Stay within workplace assistance and intelligent action, but find a more distinctive insight.

#### 3. Look for an interaction gap

Ask what becomes possible when a worker can speak naturally while the AI observes the situation, remembers context and acts through connected systems. The strongest idea should use the realtime capability as a core part of the experience, not as a voice wrapper around a form.

#### 4. Make novelty explainable in one sentence

If the unique idea takes two minutes to explain, it may not be clear enough. For SHIFTTRACE: “The maintenance system remembers the tickets; SHIFTTRACE remembers what happened.”

#### 5. Prove the difference in a live demonstration

Create a before/after moment a judge can understand immediately. For example, a second-shift technician asks what happened earlier and receives a precise, evidence-backed handoff rather than a generic summary.

#### 6. Make one end-to-end workflow real

A reliable workflow with a retrieved record, a meaningful action, approval and verified result is stronger than ten mocked capabilities.

#### 7. Treat model capability as a hypothesis

Do not assume that a multimodal model can reliably diagnose mechanical faults, identify an exact warning code from an arbitrary camera feed or recognise a bearing anomaly from phone audio. Test it. Use controlled inputs and label uncertain observations.

#### 8. Design around failure and trust

Show what happens when inventory is unavailable, a manual is ambiguous, a tool times out or the model is uncertain. Ask for confirmation before consequential action. Never narrate a failed API call as a success.

#### 9. Prioritise judge-visible proof

A judge should be able to hear the interaction, see the live context, inspect the evidence timeline and verify that the action changed a real database record.

#### 10. Keep the demo narrow and the future scope credible

The hackathon prototype can use a simulated compressor, seeded maintenance history and mock inventory. The long-term architecture can connect to real CMMS/ERP/IoT systems. Be explicit about the boundary between prototype and production.

---

## 5. Proposed demo story

### Fictional equipment

- Asset: Compressor C-204.
- Existing history: prior shift reported intermittent vibration.
- Previous action: temperature sensor replacement recorded.
- Outstanding status: symptom not confirmed as resolved.
- Demo observation: a prepared panel image or controlled live view shows a visible warning indicator.
- Demo action: replacement bearing is unavailable in local inventory.

### Three-minute demonstration

1. **Machine context:** Technician scans C-204 and asks what happened during the previous shift. The agent retrieves the earlier work order and handoff.
2. **Live interaction:** Technician points a phone camera at the prepared control panel and describes the symptom. MiniCPM or another tested vision model provides visual observations. Agora handles the live voice interaction; Murf Falcon supplies voice output.
3. **Investigation:** Agent retrieves the relevant maintenance manual section and compares the current session with prior records. It does not claim a definitive diagnosis from weak evidence.
4. **Action:** Technician asks whether a required part is available. The agent checks inventory, finds the part unavailable, prepares a procurement request and proposes updating the work order.
5. **Approval:** Technician approves. The backend submits the request and updates the work order. The application verifies both returned results.
6. **Handoff:** SHIFTTRACE creates an evidence-backed handoff. A second technician asks what happened and what remains unresolved.

### Must be demonstrably real

- Actual Agora Conversational AI session.
- Actual Murf Falcon TTS configured in Agora.
- Actual camera input reaching a vision-capable component.
- Actual model inference or clearly labelled model service.
- At least two meaningful tool/API operations.
- Persistent state change in the demo database.
- Explicit approval before the consequential action.
- A generated shift handoff that can be queried.

---

## 6. Proposed architecture principles

Do not force one model to perform every function.

### Interaction layer

- Agora Conversational AI is the required real-time voice interaction layer.
- Agora RTC carries the browser's microphone and, where implemented, camera track.
- Murf Falcon is the required voice output provider.

### Perception layer

- MiniCPM-o 4.5 is an initial model to test because it inspired the project and provides an audiovisual full-duplex demo.
- Gemini Live, Realtime-Venus, MOSS-Live and other candidates can be investigated as alternative visual/audio observers or reference architectures.
- Specialised audio anomaly models may be explored for controlled machine-sound data, but the hackathon demo should not claim a diagnostic capability that has not been validated.

### Context and memory layer

- Asset registry.
- Maintenance sessions.
- Timestamped evidence events.
- Work orders.
- Inventory.
- Manual chunks and retrieval.
- Shift handoffs.

### Agent/tool layer

- Small, well-defined tools with typed schemas.
- Read tools first; write tools only after approval.
- Idempotency keys for mutations.
- Audit log for tool calls.
- Verification after each write.

### Data provenance model

Every event should contain at minimum:

- `asset_id`
- `session_id`
- `event_id`
- `timestamp`
- `event_type`
- `source_type` (camera, microphone, technician statement, CMMS record, model inference, tool result)
- `payload`
- `confidence_or_status` where meaningful
- `model_id` and revision when model-generated
- `verified_by_user` or equivalent when a person confirms the observation

Never convert an unverified model inference into an authoritative maintenance record without review.

---

## 7. Hackathon scope and non-goals

### P0 — required for a credible submission

- Agora Conversational AI voice session.
- Murf Falcon TTS verified in the Agora agent configuration.
- Browser camera input or controlled image input to a vision component.
- MiniCPM or another tested multimodal observer for the live scene.
- One seeded asset with history and work orders.
- One maintenance knowledge retrieval path.
- Inventory lookup.
- At least one real write action such as updating a work order or creating a procurement request.
- Explicit approval for the write action.
- Verification of action outcome.
- Shift handoff generation and retrieval.
- Working demo UI and reliable recording/backup demo material.

### P1 — useful if time allows

- QR asset identification.
- Timestamped multimodal evidence timeline.
- Screenshot attachment.
- Previous-shift comparison.
- Search duplicate or related work orders.
- Discord notification.
- A second test asset.

### P2 — future research, not required for hackathon

- Real IoT telemetry.
- Dedicated microphone arrays.
- Validated acoustic anomaly detection on specific industrial equipment.
- Predictive maintenance.
- Enterprise CMMS integration.
- Cross-site operational memory.
- Mobile native application.
- Offline edge inference.

### Explicit non-goals

- Do not build a generic voice chatbot.
- Do not claim to autonomously diagnose or certify machine safety.
- Do not build a complete industrial CMMS.
- Do not integrate multiple large models before one reliable path works.
- Do not make an elaborate model catalogue.
- Do not build a fully autonomous purchasing workflow.
- Do not treat a simulated machine or mock inventory as a production integration.

---

## 8. Success metrics for the demo

| Dimension | Evidence |
|---|---|
| Problem fit | The second-shift technician can retrieve what happened without asking the previous technician to repeat everything. |
| Multimodal context | At least one useful observation from the camera or audio stream is timestamped and linked to the asset. |
| Agora usage | A real Agora Conversational AI session is used for the primary voice interaction. |
| Murf usage | Murf Falcon is configured as the TTS provider and spoken output is heard. |
| Agentic action | At least two meaningful tool/API calls occur; at least one changes persistent state. |
| Reliability | The agent verifies tool results and correctly reports failures. |
| Trust | Critical mutation requires user approval; evidence provenance is visible. |
| Continuity | A handoff is created and queried by a simulated next-shift technician. |
| Future scope | The architecture can connect to real CMMS, inventory, manuals and sensor systems. |

Do not invent numeric accuracy or latency targets. Set measurable thresholds only after establishing a baseline using the actual hardware and services.

---

## 9. Project and personal context for the coding agent

The builder is a developer with practical experience in AI agent reliability, production debugging, voice AI exploration and full-stack application development. They have an independent voice AI project called Voxie.

Voxie is an optional reference only. The SHIFTTRACE repository must be independent. The agent may inspect Voxie if the path or repository is explicitly provided, but must not modify it or make it a dependency.

The builder is interested in exploring the frontier of AI interaction: multimodal perception, real-time voice, audio/video, physical-world context and agents that can act. The hackathon solution should express that curiosity while satisfying PS31 exactly.

The builder prefers:

- A technically credible, demonstrable product over generic AI feature lists.
- An unusual but explainable insight.
- A polished, functional prototype.
- Open-source references and reproducible experiments.
- Clear separation between proven functionality and future potential.
- Direct, practical execution without unnecessary planning loops.

---

## 10. Source links and evidence notes

### Official hackathon sources

- KNOTiC event and agenda: https://buildwithagora.knotic.co/
- Commudle problem statements: https://www.commudle.com/communities/knotic/hackathons/build-with-agora-blr/tracks
- Luma event: https://luma.com/2g5vcgrr?tk=8AXBfg

### Evidence note

The PS31 wording and technology expectations in this document are drawn from the live Commudle track page checked on 19 November 2026. Event date, venue, published prize package, solo format and agenda are drawn from the KNOTiC event page checked on 19 November 2026. The five judging criteria are reproduced from the participant's supplied event information; public percentage weightings were not found.
