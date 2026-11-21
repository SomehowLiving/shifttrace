# Running cost and frontline devices

## Why it is not "live all the time"
Shifttrace does not stream a factory floor to an AI all day. A voice agent exists only while a worker is in a **session** (one job, one machine), and that is the only time anything is billed.

| What is billed | When it runs | Control |
|---|---|---|
| Agora Conversational AI task + ASR | only while the agent is in the call | **Idle pause**: after N minutes with no speech from either side (default 3), the agent is stopped and the browser leaves the call. The session and its record stay open, and **Resume voice** starts a fresh agent. **Pause** also does this on demand. Ending the session stops everything. |
| Agora RTC minutes | only while the browser is in the call | Video minutes cost about 4x audio minutes. **Camera on demand** keeps the camera off (billed as audio) until the worker taps **Show camera**, then turns it off after 60 s. |
| LLM tokens | per agent turn | Camera frames add tokens only while the camera is on. Push-to-talk avoids false turns caused by floor noise. |
| Murf Falcon voice | per character spoken | Short replies by design (one to three sentences). |

Each live session shows its **measured** estimated cost (≈ $ in the session bar, with a breakdown), from:
- the agent minutes actually used (rounded up per minute, as Agora bills)
- camera minutes reported by the browser
- characters spoken
- agent turns

**System → Running cost and cost controls** shows the per-minute, per-shift and per-month projection for the site's settings, next to what streaming a full 8-hour shift would cost.

### Default rates (public list prices; override in `backend/.env`)
| Item | Rate | Source |
|---|---|---|
| Agora Conversational AI agent task | $0.0099 / min | Agora Conversational AI pricing docs (audio basic task) |
| Agora ASR | $0.0166 / min | Agora Conversational AI pricing docs (ARES ASR task) |
| Agora RTC audio / HD video | $0.99 / $3.99 per 1,000 min | Agora voice and video calling price lists |
| Murf Falcon | $0.01 / 1,000 characters | Murf Falcon API docs |
| gpt-4o-mini | $0.15 / $0.60 per million tokens in / out | OpenAI list price; may be billed through Agora when managed |

### What "the Agora rate from your contract" means
It is the per-minute price Agora bills your Agora account for the Conversational AI agent (and, separately, ASR and RTC minutes). You find it in Agora Console:
- **Billing / Usage** shows the minutes used per product and what they cost.
- **Pricing plan / Billing center** shows the unit prices your account pays.

Accounts can differ: a sales contract, a startup or hackathon credit, or a free-minutes allowance changes the effective price. Agora's public pages also disagree: the Conversational AI pricing docs list $0.0099/min for the agent task plus $0.0166/min for ASR (with free minutes each month), while the marketing pricing page shows about $0.10/min all-in. Shifttrace uses the docs rates by default. If your Console shows a different price, set `COST_CONVOAI_PER_MIN` (and `COST_ASR_PER_MIN`) in `backend/.env`. Everything shown is an estimate, not an invoice.

With the defaults, 40 active voice minutes per worker per shift comes to about $1.40 per shift with the camera always on, and less with the camera on demand. Streaming a full 8-hour shift would be about $14.60.

## Frontline devices (for example Zebra)
- **Runs in the browser** on Android rugged mobile computers, tablets and wearables (for example Zebra TC and WS series, or ET tablets), and on any laptop. No native app is required. Microphone and camera access use the standard browser permission.
- **Barcode and QR scanning.** A code typed very fast and ending in Enter is treated as a scan. Zebra DataWedge in keystroke-output mode, or any USB or Bluetooth keyboard-wedge scanner, works without integration code.
  - On any page, scanning a machine's QR (`SHIFTTRACE:C-204`) or asset tag opens that machine.
  - During a session, scanning a part, bin or shipment label sends it to the agent ("I scanned a barcode: SKU-2231"), which looks it up.
- **Push-to-talk.** Toggle **PTT** in the voice bar, then hold Space, or map the device's programmable PTT button to F9 (on Zebra devices, through the key-remapping settings).
- **Hands-free.** It works with headsets; voice is the primary input, and barge-in is supported.
- **Workforce tools.** Verified actions go out as signed webhooks (see Connected systems) to task, messaging, ERP or CMMS platforms.
- **No scanner hardware?** The **Scan** button (sidebar, phone header and the session's voice bar) opens the device camera and reads 1D barcodes and QR codes in the browser (ZXing), with a "type a code" field and demo codes as fallbacks. **Scan and test labels** (`/labels`) prints QR labels for every demo machine, part, bin and shipment; show them on a phone and scan with a laptop camera, or tap a label to simulate the scan. All three paths use the same handler as a hardware scan.
- **Not yet tested on a physical Zebra device.** The behaviour above follows the standard DataWedge keystroke output and Android Chrome.
