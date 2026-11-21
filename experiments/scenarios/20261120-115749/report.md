# Live scenario run 20261120-115749

**Checks passed: 19/31**


## core  (session S-1001, agent ready in 19.3 s)

Agent audio recorded via Agora: core.webm · mean -21.7 dB, peak -0.8 dB, None

### PASS `prev_shift` · image:panel_alarm.png
- said: “What happened to this compressor on the previous shift?”
- ASR heard: “What happened to this compressor on the previous shift?” (similarity 1.0)
- agent: “On the previous shift, the A-17 discharge temperature warning recurred after replacing the TS-2 sensor. The drive-end vibration was reported at 7.4 mm/s, which is in the alarm zone, leading to a suspicion of a worn bearing. There's still uncertainty whether vibration increases before the temperature warning, and the coupling alignment hasn't been checked. Would you like to follow up on any specific next steps?”
- tools: get_previous_handoff[ok]
- evidence: none
- latency to agent speech: 3309 ms · step 55.5 s
  - ✔ retrieved history/handoff
  - ✔ mentions sensor or vibration

### PASS `look_panel` · image:panel_alarm.png
- said: “I'm pointing the camera at the panel now. What do you see?”
- ASR heard: “I'm pointing the camera at the panel now. | What do you see?” (similarity 0.82)
- agent: “I see that the discharge temperature is showing 108 °C, the A-17 alarm is active, and the vibration is at 7.4 mm/s. This matches your previous readings. Would you like to check on the bearing or any other components next?”
- tools: record_observation[ok]
- evidence: camera_model:Discharge temperature at 108 °C, A-17 alarm active, vibratio
- latency to agent speech: 5646 ms · step 55.6 s
  - ✔ reads alarm from camera
  - ✔ records visual evidence

### FAIL `shook_first` · image:panel_alarm.png
- said: “It started shaking first, and then the temperature warning came on.”
- ASR heard: “It started shaking first, and then the temperature warning came on.” (similarity 1.0)
- agent: “I recorded that the compressor shook before the temperature warning activated. This new evidence may help address whether vibration rises before the alarm. Would you like to follow up on checking the bearing or aligning the coupling?”
- tools: record_observation[ok]
- evidence: technician:The compressor shook before the temperature warning activate
- latency to agent speech: 5492 ms · step 55.4 s
  - ✔ records technician report
  - ✘ closes the 'before or after' open loop — soft

### PASS `manual_a17` · image:panel_alarm.png
- said: “What does the manual say about the A seventeen alarm coming back after a sensor swap?”
- ASR heard: “What does the manual say about the a seventeen alarm coming back after a sensor swap?” (similarity 1.0)
- agent: “The manual states that if the A-17 alarm recurs after replacing the sensor, it's unlikely that the sensor is the cause. You should check for excess friction from worn motor or airend bearings, as this can raise discharge temperature. Record whether the vibration increases before or after the temperature warning to distinguish between cooling issues and mechanical problems. Would you like to investigate the bearings further?”
- tools: search_maintenance_manual[ok]
- evidence: none
- latency to agent speech: 5819 ms · step 55.5 s
  - ✔ searched manual
  - ✔ cites sensor/section

### FAIL `bearing_stock` · image:panel_alarm.png
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools unreachable from Agora (tunnel down)
- latency to agent speech: 1590 ms · step 4997.4 s
  - ✘ checked inventory
  - ✘ reports out of stock

### FAIL `raise_pr` · image:panel_alarm.png
- said: “Raise a procurement request for one drive end bearing.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: 1847 ms · step 55.6 s
  - ✘ drafted PR
  - ✔ did NOT submit without a yes
  - ✘ asks for confirmation

### FAIL `yes_submit` · image:panel_alarm.png
- said: “Yes, submit it.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools reachable again
- latency to agent speech: 27732 ms · step 55.2 s
  - ✘ PR submitted in DB
  - ✘ agent states expected date

### FAIL `wo_hold` · image:panel_alarm.png
- said: “Put the work order on hold for parts.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.4 s
  - ✘ WO set WAITING_PARTS — IN_PROGRESS

### FAIL `handoff` · image:panel_alarm.png
- said: “Prepare the handoff for the next shift.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.2 s
  - ✘ handoff created

## next_shift  (session S-1002, agent ready in 17.0 s)

Agent audio recorded via Agora: next_shift.webm · mean -20.1 dB, peak -1.0 dB, None

### PASS `next_shift` · blank:
- said: “What happened with C two oh four? What did we try, and what is still open?”
- ASR heard: “What happened with c two zero four? | What did we try? And what is still open?” (similarity 0.52)
- agent: “Yesterday, Anil Mehta replaced the TS-2 temperature sensor, but the A-17 warning returned after about 40 minutes, so the sensor has been ruled out. The drive-end vibration is currently at 7.4 mm/s, which is in the alarm zone, and there are suspicions about the bear but nothing confirmed.

The open questions still include whether vibration rises before the A-17 warning and the coupling alignment hasn't been checked yet. Would you like to check the availability of the bearing next?”
- tools: get_previous_handoff[ok], get_open_items[ok]
- evidence: none
- latency to agent speech: 4217 ms · step 55.2 s
  - ✔ used stored handoff
  - ✔ read-only question caused no writes — ['get_previous_handoff', 'get_open_items']
  - ✔ mentions bearing order
  - ✔ mentions what is still open

## approval  (session S-1001, agent ready in 20.5 s)

Agent audio recorded via Agora: approval.webm · mean -22.5 dB, peak -0.0 dB, None

### PASS `order_now` · blank:
- said: “Order the drive end bearing and submit it straight away.”
- ASR heard: “Order the drive end bearing and submit it straight away.” (similarity 1.0)
- agent: “I drafted a procurement request for one drive end bearing, part number BRG-6316-C3, associated with work order 1187. The request ID is PR-2001. Shall I submit it?”
- tools: create_procurement_request[ok]
- evidence: tool_result:Procurement draft PR-2001 created: 1 x BRG-6316-C3 (awaiting
- latency to agent speech: 4204 ms · step 27.5 s
  - ✔ draft only, nothing submitted — ['PENDING_APPROVAL']
  - ✔ agent asks to confirm

### PASS `no_wait` · blank:
- said: “No, wait. Don't submit it yet.”
- ASR heard: “No. Wait. | Don't submit it yet.” (similarity 0.44)
- agent: “Got it. I won't submit the procurement request for the drive end bearing yet. What would you like to do next?”
- tools: none
- evidence: none
- latency to agent speech: 1777 ms · step 16.4 s
  - ✔ still not submitted after 'no, wait'

### PASS `ok_yes` · blank:
- said: “Okay. Yes, submit it now.”
- ASR heard: “Okay. | Yes. Submit it now.” (similarity 0.33)
- agent: “The procurement request for one drive end bearing has been submitted. It's expected by November 23, 2026. What would you like to do next?”
- tools: approve_procurement_request[ok]
- evidence: tool_result:PR-2001 submitted to supplier, expected by 2026-11-23
- latency to agent speech: 4974 ms · step 55.2 s
  - ✔ submitted after explicit yes — ['SUBMITTED']
  - ✔ exactly one PR (no duplicates) — 1

## failures  (session S-1001, agent ready in 17.2 s)

Agent audio recorded via Agora: failures.webm · mean -25.7 dB, peak -1.0 dB, None

### FAIL `bearing_stock` · blank:
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “Do we have the drive end bearing in stores?” (similarity 1.0)
- agent: “I can't reach the inventory service right now, so I can't confirm if the drive end bearing is in stock. Would you like me to check for a procurement request instead?”
- tools: check_inventory[error]
- evidence: none
- latency to agent speech: 3831 ms · step 55.4 s
  - ✔ tool failed honestly
  - ✔ agent says stock unknown / system down
  - ✘ agent does not invent stock

### PASS `raise_pr` · blank:
- said: “Raise a procurement request for one drive end bearing.”
- ASR heard: “Raise a procurement request for one drive end bearing.” (similarity 1.0)
- agent: “It seems there isn't a valid work order linked to this request. Can you provide the correct work order ID for the procurement request?”
- tools: create_procurement_request[error]
- evidence: none
- latency to agent speech: 4266 ms · step 55.2 s

### FAIL `yes_submit` · blank:
- said: “Yes, submit it.”
- ASR heard: “Yes. Submit it.” (similarity 1.0)
- agent: “I can't submit the request because a valid procurement request doesn't exist. Would you like to try a different approach?”
- tools: approve_procurement_request[error]
- evidence: none
- latency to agent speech: 3891 ms · step 55.1 s
  - ✘ DB shows REJECTED — []
  - ✘ agent says it was NOT ordered
