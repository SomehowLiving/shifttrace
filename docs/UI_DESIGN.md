# Console UI design

## Visual direction (v2, 21 Nov)
- **Calm by default, like a high-performance industrial HMI (ISA-101).** Graphite greyscale while things are normal. Colour appears only when it means something: amber needs a person, red is live or failed, green is verified, violet is model or recorded input, blue is the technician.
- **One brand accent: hi-vis safety yellow-green** (`--teal` token, `#c8f135` dark / olive `#4f6b00` light), the colour of vests and tags on the floor. It is used for the brand, the primary action, the active nav item and **one bold block per page** (on the shift board, *Needs a person first*: the machine that most needs someone, with how it got there). It never carries status.
- **Type:** Instrument Sans (variable width). Headings are set semi-condensed and tight, like an equipment nameplate; the hero uses a large display cut. Geist Mono only for real codes and small tracked labels (dates, breadcrumbs, readings).
- **Surfaces:** tonal layers (`paper` → `sheet` → `raised`) with hairlines and a faint top highlight; radius scale 7px controls, 12px panels, 16px hero blocks. No gradients, glows, grid backdrops or fake window chrome.
- **Shell:** sidebar (wordmark, Shift / Records / Setup), a top bar with the breadcrumb, the live session and "All systems nominal".
- **3D floor view** (`/floor`, also embedded on the product page under *On the floor*): a procedural three.js scene of a worker using Shifttrace at C-204, with a caption bar and a guided camera the viewer can take over. Illustration with synthetic data.

## Who uses it, and for what
- **Technician**, on a phone or laptop on the floor: talk to the agent, point the camera, approve or decline an order, and hand over at the end of the shift.
- **Next shift and supervisors**: see what each machine needs, read what the last shift left open, and check who did what.

## Flow: one trace
An earlier version split a session across three columns (camera, conversation, and evidence plus tool calls), so the reader had to match them up. The handoff appeared only at the end, and every session started with a form. The flow now centres on a single ordered log, the trace:

1. **Shift board** (`/`). The headline is the shift itself ("A shift, Saturday 21 November"). Machines that need attention come first, and each shows what the last shift left open, as the actual questions rather than a count, plus the handover headline. Click **Open C-204**.
2. **Machine** (`/machines/:id`). On the right is **Start a session**. Who is on shift is set once in the header (On shift: Kavya Rao, A shift), so this panel only asks what the session is for. The usual task for the machine is preselected, and the voice agent is on by default. On the left: **Still open** (questions no shift has closed), then the **Log**, which is every earlier shift as a ruled band with its entries in order, ending with the handover headline.
3. **Session** (`/session/:id`). The main column is **This session, in order**: what the technician said (quoted, in blue ink), what the agent said, each lookup as a short line, and every piece of evidence and verified change, all on one trace line that ends at a pulsing **now**. An approval card pins under the trace until someone decides it. The right column has the camera, the agent's state (ready, listening, thinking or speaking, shown with motion and a word) and **Handoff so far**, which fills in live with still open, done and verified, seen and said, and not done. **Finish and hand over** writes the handoff, ends the session and opens the handoff.
4. **Handoff** (`/handoffs/:id`). A filed sheet that reads still open first, then not done, done and verified, seen and said, parts, next steps and the spoken summary. At the bottom, **Hand over C-204** takes the next technician's name and starts their briefing (the read-and-note-only task) in one step.

**Test feed.** Most people trying Shifttrace have no machine to hand. With the test feed on (the default), the session's right column gains **Test feed**: thumbnails choose what the camera shows, and **Say for me** plays recorded questions as the technician's voice. It is marked in violet, the colour used for model and recorded input, and the header says "(test feed)" so a test session is never mistaken for a real one.

Secondary pages: **Stores and orders** (pending approvals pinned at the top, then orders, stock with out-of-stock first, and work orders); **Audit log**, which lists every tool call with filters for result, who made it, session and free text, plus an inspector, and marks a change verified only after a fresh-connection read-back; and **System**, which holds the live checks, failure switches, reset and loaded packs.

## Product page and console shell (current)
- `/` is the product page for judges and first visitors. It leads with an animated preview of a real session rather than a stock dashboard picture. Every claim on it maps to a mechanism in the code (approval gate, re-read writes, claim guard), and the numbers are counted live from the database.
- `/board` and every other page except a live session sit in a sidebar shell: Shift board; Records (Audit log, Orders and stock, Handoffs); Setup.
- The Shift board is an operations dashboard: live sessions, attention, open questions, verified changes, pending approvals, machine cards, live activity.
- Type is Geist and Geist Mono. The dark palette is near-black with teal as the brand and verified colour. Amber means a person is needed or something is unverified, red means live or failed, and violet means model or recorded input.

## Session console
The live session is a focused workspace with no site navigation, laid out as three panels and a bottom voice bar:

```
┌ ← Shift board │ ● LIVE SESSION │ S-1003 │ Compressor C-204 │ Troubleshoot ▾ │ TEST FEED     00:04:32  Audit log  End without handoff  [Finish and hand over] ┐
│ MACHINE                 │ SESSION TRACE                                         │ MACHINE CAMERA                  │
│ C-204  ◆ degraded       │ 08:58 (mic)  “What happened last shift?”     Speech   │ [ panel A-17 108 °C ]           │
│ Overview | Safety+manual│ 08:58 (db)   Read the previous handoff       Lookup   │ test feed scenes ▸ thumbnails   │
│ make, model, WO         │ 08:58 (eye)  108 °C, out of limit [frame]  Camera ◇  │ HANDOFF SO FAR                  │
│ previous shift          │ 08:58 (bulb) follow up?            AI hypothesis ◌    │ still open / done / seen / not  │
│ still open              │ ┌ Approval required: 1 × bearing … [Approve][Decline]┐│                                 │
├─────────────────────────┴───────────────────────────────────────────────────────┴─────────────────────────────────┤
│ ▁▃▅▇▅▃ Listening…   (( MIC ))   [cam] [Capture evidence]   [type to the agent…]   [▶ Test feed: say line 3 of 18] ^ │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Rules the reference mockup broke, and how they are handled here:
- AI analysis is never shown with a green tick. Hypotheses carry an amber dashed ring and "AI hypothesis".
- There is one way to finish, not two end buttons.
- Approvals have on-screen buttons as well as voice.
- Machine data stays fictional.

On a phone the order is camera, trace, handoff so far, then machine, with the voice bar fixed at the bottom.

Navigation is **Shift board** and **Records** (Audit log, Orders and stock, Handoffs as tabs), plus System in the header. Dark operations is the default theme; the light logbook theme is one click away.

## Look: the shift logbook (earlier pass, still the light theme)
The visual source is a paper shift log: a time column in the margin, a ruled band for each shift, and one continuous line joining the entries. Ink on cool paper-white (not cream). Sections are separated by a heavy ink rule rather than drawn as cards. The handoff is the one place drawn as a sheet, because it is a filed document.

| Token | Light | Use |
|---|---|---|
| paper | `#f4f6f5` | page |
| sheet | `#fbfcfb` | the handoff sheet, shift bands, inputs |
| ink | `#16202a` | text, rules, primary buttons |
| pencil | `#66717b` | times, secondary text |
| red | `#b3261e` | live, failed, claim check failed, safety |
| ochre | `#a26400` (wash `#f6e7c8`) | still open, needs approval, degraded |
| green | `#2c6a3f` | verified by re-reading the database |
| violet | `#5a4aa6` | model readings, unverified |
| blue | `#1d4f8f` | the technician's words, links |

Night mode keeps the same roles. **Type:** Atkinson Hyperlegible Next, self-hosted. It was designed for legibility under poor conditions, which suits glare, distance and gloves on a plant floor. One family; times use a 24-hour clock, as plants do.

## Marks
Every entry on the trace has a mark showing where it came from, and the same marks are used on every page ("What the marks mean" explains them):

| Mark | Meaning |
|---|---|
| filled blue circle | technician |
| hollow ink circle | Shifttrace (the agent) speaking |
| outline violet diamond | camera or audio, model reading: unverified, not a diagnosis |
| dashed ochre ring | AI hypothesis |
| teal square | system record |
| green box with a tick | verified change |
| short grey tick | a lookup (manual, stock, history) |
| red triangle | failed call or claim check failed |

States are always colour, shape and a word together, such as a stamp reading "◆ needs approval", so nothing depends on colour alone.

## Sources consulted
- Anthropic `frontend-design` skill (github.com/anthropics/skills, Apache-2.0), installed at `~/.claude/skills/frontend-design`: ground the design in the subject, spend boldness in one place (here, the trace), and avoid template chrome such as card grids, all-caps labels and near-black with a single accent.
- ISA-101 and high-performance HMI summaries: neutral by default, colour for abnormal states, and colour paired with shape and text.
- Audit-log UX patterns: who did what to which record and with what result, day dividers, filters by actor and result, and saying what the log covers.
