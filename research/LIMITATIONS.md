# Limitations and unverified claims

## Found in live testing (19–20 Nov)
- **The LLM will invent tool results if it has no tools.** Observed live. Mitigated by the start gate, tool-link verification, watchdog and claim guard, but the guard is pattern-based (English phrasing) and acts after the sentence is spoken; it corrects, it cannot un-say.
- **Free Cloudflare quick tunnels are not reliable enough for the demo.** Agora intermittently cannot reach them; one died mid-run. Use a stable public endpoint (ngrok reserved domain, Cloudflare named tunnel, or deploy the MCP server).
- Answers that need tools still take ~5–7 s in total; filler words bring the first audio to ~1.75 s.
- Visual evidence auto-captured from the agent's speech depends on English phrasing patterns (camera question + visual description); it records what the model *said*, labelled as such.
- **Frame lag:** after the camera view changes, the model can describe the previous frame for a few seconds (seen at 2.5 s; not seen at 6 s). Technicians should hold the camera steady ~5 s before asking.
- Camera frames are not available to the LLM for the first seconds of a session ("I haven't received any visual input yet").

## Previously unverified, now verified live
- Agora forwards camera frames to gpt-4o-mini well enough to read the simulated panel and real photos.
- gpt-4o-mini follows draft → read-back → approve; the server-side gate held in adversarial phrasing.
- Murf voice `en-IN-isha` (the docs' `Matthew` does not exist on this account).

## Originally unverified
- That Agora forwards frames from the published camera track to the managed LLM at a rate and resolution good enough to read the panel. Source: the official Vision Recipe README and agent code. A third-party note in our research brief said a recipe test used a synthetic pattern without exercising image understanding.
- That gpt-4o-mini reliably calls the MCP tools with the arguments we expect, and respects "draft, read back, then approve".
- Murf Falcon voice `Matthew` exists on the account (preflight checks this).
- End-to-end latency. No numbers are claimed.

## Design limitations
- **Spoken approval heuristic.** Approval = latest final technician utterance after the agent's read-back matches an affirmative pattern and no negation. A "yes" given to a different question asked after the draft would count. Mitigation: the prompt forbids approving in the same turn; the console card is always available; the evidence string records the exact words used.
- Approval depends on the browser relaying RTM transcripts. If RTM is down, voice approval is impossible and the agent is told to use the console button.
- Typed messages are treated as the technician's words (they come from the technician's console).
- Single active session at a time (demo scope). Starting a new session ends the previous one.
- Snapshot attached to a visual observation is the latest browser frame (taken at most 20 s earlier), not necessarily the exact frame Agora sent to the LLM.
- No authentication on the console (localhost only). Production needs SSO and per-technician identity.
- Inventory, suppliers and the manual are synthetic. The "supplier submission" is a database state change, not an external API.
- No audio anomaly detection: sounds are captured only as technician statements.
- Quick tunnels have no uptime guarantee.

## Safety position
The agent never diagnoses or certifies equipment as safe. Hypotheses stay labelled until a person confirms them. Bearing/coupling work prompts a lockout/tagout reminder. Closing a work order is not possible by voice.
