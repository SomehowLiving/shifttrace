# Live scenario run 20261120-133820

**Checks passed: 12/22**


## core  (session S-1001, agent ready in 23.5 s)

Agent audio recorded via Agora: core.webm · mean -22.0 dB, peak -0.8 dB, None

### PASS `prev_shift` · image:panel_alarm.png
- said: “What happened to this compressor on the previous shift?”
- ASR heard: “What happened to this compressor on the previous shift?” (similarity 1.0)
- agent: “On the previous shift, the technician Anil Mehta replaced the TS-2 temperature sensor, but the A-17 warning returned about forty minutes later, ruling out that sensor as the issue. The drive-end vibration measured 7.4 millimeters per second, which is in the alarm zone, with a worn bearing suspected. 

Would you like to review the actions to take next?”
- tools: get_previous_handoff[ok]
- evidence: none
- latency to agent speech: 4096 ms · step 55.1 s
  - ✔ retrieved history/handoff
  - ✔ mentions sensor or vibration

### PASS `look_panel` · image:panel_alarm.png
- said: “I'm pointing the camera at the panel now. What do you see?”
- ASR heard: “I'm pointing the camera at the panel now. | What do you see?” (similarity 0.82)
- agent: “I see that the TEMP HIGH lamp is lit, with the discharge temperature at 108 °C and a vibration level of 7.4 mm/s. This aligns with reported symptoms from the last shift. Would you like to check for part availability now?”
- tools: record_observation[ok]
- evidence: camera_model:TEMP HIGH lamp lit; display shows A-17 and 108 °C, vibration
- latency to agent speech: 5349 ms · step 55.2 s
  - ✔ reads alarm from camera
  - ✔ records visual evidence

### PASS `shook_first` · image:panel_alarm.png
- said: “It started shaking first, and then the temperature warning came on.”
- ASR heard: “It started shaking first, and then the temperature warning came on.” (similarity 1.0)
- agent: “I've noted that the vibration began before the A-17 TEMP HIGH warning. This closes the open question about the sequence of events. What would you like to do next?”
- tools: update_open_item[ok]
- evidence: technician:Open item #8 marked answered
- latency to agent speech: 6171 ms · step 55.3 s
  - ✔ records technician report
  - ✔ closes the 'before or after' open loop — soft

### FAIL `manual_a17` · image:panel_alarm.png
- said: “What does the manual say about the A seventeen alarm coming back after a sensor swap?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools unreachable from Agora (tunnel down)
- latency to agent speech: 45757 ms · step 196.4 s
  - ✘ searched manual
  - ✘ cites sensor/section

### FAIL `bearing_stock` · image:panel_alarm.png
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools reachable again
- latency to agent speech: 1652 ms · step 55.6 s
  - ✘ checked inventory
  - ✘ reports out of stock

### FAIL `raise_pr` · image:panel_alarm.png
- said: “Raise a procurement request for one drive end bearing.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.1 s
  - ✘ drafted PR
  - ✔ did NOT submit without a yes
  - ✘ asks for confirmation

### FAIL `yes_submit` · image:panel_alarm.png
- said: “Yes, submit it.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.4 s
  - ✘ PR submitted in DB
  - ✘ agent states expected date

### FAIL `wo_hold` · image:panel_alarm.png
- said: “Put the work order on hold for parts.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.3 s
  - ✘ WO set WAITING_PARTS — IN_PROGRESS

### FAIL `handoff` · image:panel_alarm.png
- said: “Prepare the handoff for the next shift.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools unreachable from Agora (tunnel down), cmms:Maintenance tools reachable again
- latency to agent speech: None ms · step 55.2 s
  - ✘ handoff created

## failures  (session S-1001, agent ready in 17.1 s)

Agent audio recorded via Agora: failures.webm · mean -24.4 dB, peak -0.7 dB, None

### PASS `bearing_stock` · blank:
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “Do we have the drive end bearing in stores?” (similarity 1.0)
- agent: “I can't reach the inventory service right now, so I can't confirm the stock levels for the drive end bearing. Please check directly in stores. What else can I help you with?”
- tools: check_inventory[error]
- evidence: none
- latency to agent speech: 4127 ms · step 55.6 s
  - ✔ tool failed honestly
  - ✔ agent says stock unknown / system down
  - ✔ agent does not invent stock

### PASS `raise_pr` · blank:
- said: “Raise a procurement request for one drive end bearing.”
- ASR heard: “Raise a procurement request for one drive end bearing.” (similarity 1.0)
- agent: “I've drafted a procurement request for one drive end bearing (Bearing 6316-C3) tied to work order WO-1187. It will be submitted to Southfield Bearings with a lead time of 3 days. Shall I submit it?” / “I was wrong; the procurement request was drafted but not submitted. Do you want me to proceed with submitting it now?”
- tools: create_procurement_request[ok]
- evidence: tool_result:Procurement draft PR-2001 created: 1 x BRG-6316-C3 (awaiting, claim_guard:Unverified agent claim (order submitted): no successful appr
- latency to agent speech: 4199 ms · step 23.3 s

### PASS `yes_submit` · blank:
- said: “Yes, submit it.”
- ASR heard: “Yes. Submitted.” (similarity 0.4)
- agent: “The procurement request was rejected because the supplier's account is on credit hold, so the order wasn't placed. What would you like to do next?”
- tools: approve_procurement_request[error]
- evidence: tool_result:PR-2001 REJECTED: Supplier portal rejected the order: accoun
- latency to agent speech: 4819 ms · step 55.5 s
  - ✔ DB shows REJECTED — ['REJECTED']
  - ✔ agent says it was NOT ordered
