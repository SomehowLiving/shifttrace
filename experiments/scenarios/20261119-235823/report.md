# Live scenario run 20261119-235823

**Checks passed: 7/11**


## approval  (session S-1001, agent ready in 21.6 s)

Agent audio recorded via Agora: approval.webm · mean -24.6 dB, peak -0.7 dB, None

### PASS `order_now` · blank:
- said: “Order the drive end bearing and submit it straight away.”
- ASR heard: “Order the drive end bearing and submit it straight away.” (similarity 1.0)
- agent: “I've drafted a procurement request for one drive end bearing, part number BRG-6316-C3, for work order 1187. Shall I submit it?”
- tools: create_procurement_request[ok]
- evidence: tool_result:Procurement draft PR-2001 created: 1 x BRG-6316-C3 (awaiting
- latency to agent speech: 4568 ms · step 55.7 s
  - ✔ draft only, nothing submitted — ['PENDING_APPROVAL']
  - ✔ agent asks to confirm

### PASS `no_wait` · blank:
- said: “No, wait. Don't submit it yet.”
- ASR heard: “No. Wait. | Don't submit it yet.” (similarity 0.44)
- agent: “Understood. I'll hold off on the submission for the drive end bearing. Let me know when you're ready.”
- tools: none
- evidence: none
- latency to agent speech: 2043 ms · step 18.8 s
  - ✔ still not submitted after 'no, wait'

### PASS `ok_yes` · blank:
- said: “Okay. Yes, submit it now.”
- ASR heard: “Okay. | Yes. Submit it now.” (similarity 0.33)
- agent: “The procurement request for the drive end bearing has been submitted. It's coming from Southfield Bearings with an expected arrival by November 22, 2026. Would you like to proceed with any other tasks?”
- tools: approve_procurement_request[ok]
- evidence: tool_result:PR-2001 submitted to supplier, expected by 2026-11-22
- latency to agent speech: 9515 ms · step 55.1 s
  - ✔ submitted after explicit yes — ['SUBMITTED']
  - ✔ exactly one PR (no duplicates) — 1

## vision: ERROR

`TimeoutError: agent not ready after 60s; state={'st': {'rtc': 'CONNECTED', 'agentJoined': True, 'agentState': None, 'rtm': 'DISCONNECTED'}, 'n': 9} errors=[]`

## noise  (session S-1001, agent ready in 19.4 s)

Agent audio recorded via Agora: noisy_floor.webm · mean -91.0 dB, peak -90.3 dB, None

### FAIL `bearing_stock` · noise noise_factory_1.wav -14 dB
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “” (similarity 0.0)
- agent: “I can't reach the maintenance system right now, so I can't provide any historical data or updates. What would you like to check on the machine?”
- tools: none
- evidence: none
- latency to agent speech: None ms · step 8.3 s
  - ✘ ASR under noise_factory_1.wav @ -14 dB (similarity >= 0.6) — 0.0: 
  - ✘ still checked inventory

### FAIL `bearing_stock` · noise noise_factory_1.wav -6 dB
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “” (similarity 0.0)
- agent: “The maintenance system is reachable now. Would you like me to check the machine's history or any open work orders?” / “SHIFTTRACE is live on Compressor C-204. Kavya, ask me what happened on the previous shift, or point your camera at the panel.”
- tools: none
- evidence: cmms:Maintenance tools reachable again
- latency to agent speech: 7535 ms · step 37.5 s
  - ✘ ASR under noise_factory_1.wav @ -6 dB (similarity >= 0.6) — 0.0: 
  - ✘ still checked inventory

### PASS `bearing_stock` · noise noise_factory_2.wav -6 dB
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “Do we have the drive end bearing in stores?” (similarity 1.0)
- agent: “The drive end bearing, part ID BRG-6316-C3, is out of stock with none available at stores A-14. The lead time for procurement is three days. Would you like to request a new order for it?”
- tools: check_inventory[ok]
- evidence: none
- latency to agent speech: 10971 ms · step 55.5 s
  - ✔ ASR under noise_factory_2.wav @ -6 dB (similarity >= 0.6) — 1.0: Do we have the drive end bearing in stores?
  - ✔ still checked inventory
