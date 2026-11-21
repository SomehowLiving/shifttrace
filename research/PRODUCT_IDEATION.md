# Product ideation (time-boxed, 19 Nov 2026)

Constraint: PS31 is fixed (Before → During → Action → After). We are choosing *how* to solve it.

## What actually goes wrong in a maintenance shift change

- The CMMS keeps the **outcome** ("sensor replaced") but not the **reasoning** ("warning came back 40 min later, so the sensor was not the cause").
- Ruled-out hypotheses are lost, so the next shift repeats the same checks.
- Open questions ("does vibration start before the warning?") live only in someone's head.
- Parts status (requested? approved? ETA?) is in a different system from the work order.
- The technician's hands are busy and gloved; stopping to type is the reason notes are thin.

## Alternatives considered

| # | Concept | Problem fit | Innovation | Agora voice is essential? | Functionality risk | Verdict |
|---|---|---|---|---|---|---|
| A | **Operational memory across shifts** (baseline SHIFTTRACE): timeline of evidence + handoff | High: covers all four PS31 stages | Medium: "handoff" alone sounds like a report generator | Yes: hands-free capture | Low | Keep as the spine |
| B | **Camera-verified procedure guidance** (agent checks each LOTO/inspection step through the camera) | Medium: mostly the "During" stage | High | Yes | **High**: a phone camera can't reliably verify safety steps, and getting it wrong is a safety claim | Reject (unsafe claim) |
| C | **"Talk to the machine"**: the asset answers in the first person from its history | Medium | Memorable but gimmicky | Yes | Low | Reject as the core; maybe a line in the pitch |
| D | **Open-loop ledger**: memory tracks the *epistemic status* of every finding (observed / reported / system record / AI inference; open / ruled-out / confirmed). The shift cannot be handed over with silent gaps; the agent asks about open loops before closing | High: sharpens "After" and "Before" | **High**: few CMMS/copilots model *what we still don't know* | Yes: the agent interviews the technician hands-free | Low-medium | **Merge into A** |

## Selected direction: SHIFTTRACE = A + D

> The maintenance system remembers the tickets. SHIFTTRACE remembers what actually happened, **and what is still unknown.**

What it adds on top of a "field technician copilot":

1. **Provenance on every memory item.** Each evidence event records where it came from: a camera frame read by a model, the technician's words, a system record, an AI hypothesis, or a tool result. The UI and the handoff keep them visually separate.
2. **Open loops are first-class.** Hypotheses and questions stay `open` until someone marks them `confirmed` or `ruled_out`. The handoff is organised around open loops, not a prose summary.
3. **Verified actions only.** Procurement and work-order changes are re-read from the database before the agent may say "done". Approval is a server-side gate tied to the technician's own words (transcript) or a console click. The LLM cannot approve its own action.
4. **The next shift starts with a voice briefing**, not a page of tickets.

Judge-visible "aha": the second technician says "What happened with C-204, what did we try, and what's still open?" The agent answers from the stored handoff, with each claim tied to its source, including the open question the first technician never answered.

Decision: committed. No further concept exploration during the build.
