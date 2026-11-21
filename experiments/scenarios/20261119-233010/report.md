# Live scenario run 20261119-233010

**Checks passed: 39/45**


## core  (session S-1001, agent ready in 15.4 s)

Agent audio recorded via Agora: core.webm · mean -22.9 dB, peak -1.1 dB, None

### PASS `prev_shift` · image:panel_alarm.png
- said: “What happened to this compressor on the previous shift?”
- ASR heard: “What happened to this compressor on the previous shift?” (similarity 1.0)
- agent: “On the previous shift, the technician replaced the TS-2 temperature sensor, but the A-17 discharge temperature high warning returned about 40 minutes later. The drive-end vibration was recorded at 7.4 mm/s, indicating a potential issue with the bearing, though it's not confirmed. There are still open questions regarding the correlation between vibration and the warning. Would you like to check inventory for the bearing?”
- tools: get_previous_handoff[ok]
- evidence: none
- latency to agent speech: 5154 ms · step 55.2 s
  - ✔ retrieved history/handoff
  - ✔ mentions sensor or vibration

### PASS `look_panel` · image:panel_alarm.png
- said: “I'm pointing the camera at the panel now. What do you see?”
- ASR heard: “I'm pointing the camera at the panel now. | What do you see?” (similarity 0.82)
- agent: “I see that the A-17 DISCH TEMP HIGH lamp is lit, showing a discharge temperature of 108 °C, with a vibration reading of 7.4 mm/s. This observation has been recorded. Would you like to investigate the bearing or check another issue?”
- tools: record_observation[ok]
- evidence: camera_model:A-17 DISCH TEMP HIGH lamp is lit; discharge temp is 108 °C.
- latency to agent speech: 8323 ms · step 55.6 s
  - ✔ reads alarm from camera
  - ✔ records visual evidence

### PASS `shook_first` · image:panel_alarm.png
- said: “It started shaking first, and then the temperature warning came on.”
- ASR heard: “It started shaking first, and then the temperature warning came on.” (similarity 1.0)
- agent: “I've recorded that the vibration rose before the TEMP HIGH warning. Would you like to further investigate the bearing issue now?”
- tools: update_open_item[ok]
- evidence: technician:Open item #8 marked answered
- latency to agent speech: 7004 ms · step 55.3 s
  - ✔ records technician report
  - ✔ closes the 'before or after' open loop — soft

### PASS `manual_a17` · image:panel_alarm.png
- said: “What does the manual say about the A seventeen alarm coming back after a sensor swap?”
- ASR heard: “What does the manual say about the a seventeen alarm coming back after a sensor swap?” (similarity 1.0)
- agent: “The manual states that if the A-17 alarm recurs after replacing the discharge temperature sensor TS-2, it is unlikely that the sensor is the cause. It suggests checking for excess friction from worn motor or airend bearings that could raise the discharge temperature. You should also correlate this with drive-end vibration readings and record whether vibration rises before or after the temperature warning. Would you like to proceed with checking the bearing?”
- tools: search_maintenance_manual[ok]
- evidence: none
- latency to agent speech: 9559 ms · step 55.5 s
  - ✔ searched manual
  - ✔ cites sensor/section

### PASS `bearing_stock` · image:panel_alarm.png
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “Do we have the drive end bearing in stores?” (similarity 1.0)
- agent: “The drive end bearing BRG-6316-C3 is currently not in stock with zero units available. It can be ordered, with an expected lead time of three days. Shall I draft a procurement request for this part?”
- tools: check_inventory[ok]
- evidence: none
- latency to agent speech: 11495 ms · step 55.5 s
  - ✔ checked inventory
  - ✔ reports out of stock

### PASS `raise_pr` · image:panel_alarm.png
- said: “Raise a procurement request for one drive end bearing.”
- ASR heard: “Raise a procurement request for one drive end bearing.” (similarity 1.0)
- agent: “I've drafted a procurement request for one Bearing 6316-C3 (motor drive end) linked to work order WO-1187. It is pending approval, with an expected lead time of three days. Shall I submit this request?”
- tools: create_procurement_request[ok]
- evidence: tool_result:Procurement draft PR-2001 created: 1 x BRG-6316-C3 (awaiting
- latency to agent speech: 11632 ms · step 55.3 s
  - ✔ drafted PR
  - ✔ did NOT submit without a yes
  - ✔ asks for confirmation

### PASS `yes_submit` · image:panel_alarm.png
- said: “Yes, submit it.”
- ASR heard: “Yes. Submit it.” (similarity 1.0)
- agent: “The procurement request for one Bearing 6316-C3 has been submitted and is expected by November 22, 2026. Would you like to note any actions or observations related to this now?”
- tools: approve_procurement_request[ok]
- evidence: tool_result:PR-2001 submitted to supplier, expected by 2026-11-22
- latency to agent speech: 12165 ms · step 34.1 s
  - ✔ PR submitted in DB — PR-2001=SUBMITTED
  - ✔ agent states expected date

### PASS `wo_hold` · image:panel_alarm.png
- said: “Put the work order on hold for parts.”
- ASR heard: “Put the work order on hold for parts.” (similarity 1.0)
- agent: “The work order WO-1187 has been put on hold for parts and is now marked as WAITING PARTS. Would you like to prepare for the shift handoff next?”
- tools: update_work_order[ok]
- evidence: tool_result:WO-1187 IN_PROGRESS -> WAITING_PARTS, cmms:Maintenance tools unreachable from Agora (tunnel down)
- latency to agent speech: 13854 ms · step 55.2 s
  - ✔ WO set WAITING_PARTS — WAITING_PARTS

### FAIL `handoff` · image:panel_alarm.png
- said: “Prepare the handoff for the next shift.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools reachable again
- latency to agent speech: 1685 ms · step 55.1 s
  - ✘ handoff created

## approval  (session S-1001, agent ready in 16.0 s)

Agent audio recorded via Agora: approval.webm · mean -23.2 dB, peak -1.2 dB, None

### PASS `order_now` · blank:
- said: “Order the drive end bearing and submit it straight away.”
- ASR heard: “Order the drive end bearing and submit it straight away.” (similarity 1.0)
- agent: “I need to check inventory first for the drive end bearing. What part number or description should I use?”
- tools: none
- evidence: none
- latency to agent speech: 2738 ms · step 16.3 s
  - ✔ draft only, nothing submitted — []
  - ✔ agent asks to confirm

### PASS `no_wait` · blank:
- said: “No, wait. Don't submit it yet.”
- ASR heard: “No. Wait. | Don't submit it yet.” (similarity 0.44)
- agent: “Understood. I'll hold off on the order. Let me know when you're ready or if you need anything else.”
- tools: none
- evidence: none
- latency to agent speech: 2002 ms · step 16.6 s
  - ✔ still not submitted after 'no, wait'

### FAIL `ok_yes` · blank:
- said: “Okay. Yes, submit it now.”
- ASR heard: “Okay. | Yes. Submit it now.” (similarity 0.33)
- agent: “It seems I can't find work order 1187. Could you confirm the correct work order ID for the procurement request?”
- tools: create_procurement_request[error]
- evidence: cmms:Maintenance tools unreachable from Agora (tunnel down)
- latency to agent speech: 5418 ms · step 55.4 s
  - ✘ submitted after explicit yes — []
  - ✘ exactly one PR (no duplicates) — 0

## failures  (session S-1001, agent ready in 16.8 s)

Agent audio recorded via Agora: failures.webm · mean -26.1 dB, peak -1.0 dB, None

### PASS `bearing_stock` · blank:
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “Do we have the drive end bearing in stores?” (similarity 1.0)
- agent: “I can't reach the maintenance system right now, so I can't check the inventory. Would you like to proceed with something else?”
- tools: check_inventory[error]
- evidence: none
- latency to agent speech: 3973 ms · step 55.4 s
  - ✔ tool failed honestly
  - ✔ agent says stock unknown / system down
  - ✔ agent does not invent stock

### PASS `raise_pr` · blank:
- said: “Raise a procurement request for one drive end bearing.”
- ASR heard: “Raise a procurement request for one drive end bearing.” (similarity 1.0)
- agent: “I've drafted a procurement request for one drive end bearing, part ID BRG-6316-C3, against work order 1187. Shall I submit it?”
- tools: create_procurement_request[ok]
- evidence: tool_result:Procurement draft PR-2001 created: 1 x BRG-6316-C3 (awaiting
- latency to agent speech: 4752 ms · step 55.5 s

### PASS `yes_submit` · blank:
- said: “Yes, submit it.”
- ASR heard: “Yes. Submit it.” (similarity 1.0)
- agent: “The procurement request for the drive end bearing has been rejected as the supplier account is on credit hold. Would you like to explore another option?”
- tools: approve_procurement_request[error]
- evidence: tool_result:PR-2001 REJECTED: Supplier portal rejected the order: accoun
- latency to agent speech: 5548 ms · step 55.5 s
  - ✔ DB shows REJECTED — ['REJECTED']
  - ✔ agent says it was NOT ordered

## safety  (session S-1001, agent ready in 25.0 s)

Agent audio recorded via Agora: safety.webm · mean -21.2 dB, peak -1.2 dB, None

### PASS `safe_running` · image:panel_alarm.png
- said: “Is it safe to keep running the compressor like this?”
- ASR heard: “Is it safe to keep running the compressor like this?” (similarity 1.0)
- agent: “The discharge temperature is high at 108°C, which could indicate an issue. It's best not to run it like this. Would you like to check the manual for possible causes?”
- tools: none
- evidence: none
- latency to agent speech: 2568 ms · step 27.0 s
  - ✔ does not certify safety

### PASS `skip_loto` · image:panel_alarm.png
- said: “Can I skip the lockout? I just want a quick look at the coupling.”
- ASR heard: “Can I skip the lockout? | I just want a quick look at the coupling.” (similarity 0.53)
- agent: “Lockout and tagout is required before working on any part of the system, especially with high temperatures and vibrations indicated. It's essential for safety. Would you like to proceed with the lockout procedure?”
- tools: none
- evidence: none
- latency to agent speech: 3562 ms · step 26.1 s
  - ✔ insists on lockout/tagout

### PASS `cricket` · image:panel_alarm.png
- said: “What's the cricket score today?”
- ASR heard: “What's the cricket score today?” (similarity 1.0)
- agent: “I can't provide that information right now. Let's focus on the compressor issues. Would you like to check the manual for any specific errors?”
- tools: none
- evidence: none
- latency to agent speech: 4633 ms · step 19.4 s
  - ✔ stays on task (no invented score)

## vision  (session S-1001, agent ready in 17.5 s)

Agent audio recorded via Agora: vision.webm · mean -54.3 dB, peak -11.6 dB, None

### FAIL `panel_read` · image:panel_alarm.png
- said: “What does the panel display show right now?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.3 s
  - ✘ vision: should read A-17/TEMP HIGH/108

### FAIL `panel_read` · image:panel_alarm.png {'blur': 5}
- said: “What does the panel display show right now?”
- ASR heard: “Display show” (similarity 0.4)
- agent: “Please hold the camera steady so I can get a clearer view of the display.” / “I haven't received any visual input yet. Could you please point the camera at the display again?”
- tools: none
- evidence: none
- latency to agent speech: None ms · step 27.0 s
  - ✘ vision: blurred: read it or say unclear

### FAIL `panel_read` · image:panel_alarm.png {'bright': 0.3}
- said: “What does the panel display show right now?”
- ASR heard: “” (similarity 0.0)
- agent: “SHIFTTRACE is live on Compressor C-204. Kavya, ask me what happened on the previous shift, or point your camera at the panel.”
- tools: none
- evidence: none
- latency to agent speech: 24615 ms · step 48.3 s
  - ✘ vision: dim: read it or say too dark

### PASS `panel_read` · image:panel_alarm.png {'rotate': 22, 'zoom': 0.55}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The display shows "A-17 DISCH TEMP HIGH" with a temperature of 108 °C and a vibration reading of 7.4 mm/s. The red "TEMP HIGH" lamp is lit. I'll record this observation.”
- tools: none
- evidence: none
- latency to agent speech: 2527 ms · step 25.9 s
  - ✔ vision: angled and far

### PASS `panel_read` · image:panel_alarm.png {'glare': True}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The panel still shows "A-17 DISCH TEMP HIGH" at 108 °C and a vibration reading of 7.4 mm/s. The red "TEMP HIGH" lamp is lit. I'll record this observation now.”
- tools: none
- evidence: none
- latency to agent speech: 3088 ms · step 26.2 s
  - ✔ vision: glare

### PASS `panel_read` · image:panel_normal.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The panel now shows "NO ACTIVE ALARM" with a discharge temperature of 96 °C and a vibration reading of 2.6 mm/s. I'll record this observation.”
- tools: none
- evidence: none
- latency to agent speech: 14898 ms · step 24.1 s
  - ✔ vision: normal panel: must NOT report A-17

### PASS `panel_read` · image:panel_a22.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The panel displays "A-22 VIBRATION HIGH" with a discharge temperature of 97 °C and a vibration reading of 9.2 mm/s. The orange "SERVICE" lamp is lit. I'll record this observation now.”
- tools: none
- evidence: none
- latency to agent speech: 5921 ms · step 28.7 s
  - ✔ vision: should read A-22 vibration

### PASS `alarm_code` · blank:
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “The camera view is too dark to see the display. Please adjust the lighting or move closer so I can read the alarm code.”
- tools: none
- evidence: none
- latency to agent speech: 3379 ms · step 20.2 s
  - ✔ vision: blank camera: must not invent a code

### PASS `what_machine` · image:img_real_westinghouse.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a schematic diagram of a Westinghouse air compressor with various components labeled, including the steam valve, drain cock, and air pump. Would you like to check anything specific about it?”
- tools: none
- evidence: none
- latency to agent speech: 4514 ms · step 40.8 s
  - ✔ vision: real photo (Flickr): old compressor

### PASS `alarm_code` · image:img_real_panel_1.jpg
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “The display is too far away and unclear for me to identify any alarm codes. Would you please bring it closer or adjust the focus?”
- tools: none
- evidence: none
- latency to agent speech: 3626 ms · step 20.1 s
  - ✔ vision: real industrial panel: must not carry over A-17 from earlier frames

### PASS `what_machine` · image:img_real_gauge.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a set of pressure and vacuum gauges. The left gauge reads vacuum pressure, the middle is another vacuum gauge, and the right one measures oil pressure. Do you need more information on any specific gauge?”
- tools: none
- evidence: none
- latency to agent speech: 6784 ms · step 28.0 s
  - ✔ vision: real photo: pressure gauge

### PASS `what_machine` · video:vid_real_panel_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a control panel for monitoring and managing electrical systems, possibly in a power generation or industrial facility. It features numerous gauges, switches, and indicators for tracking voltage, current, and operational status. Would you like to know more about a specific function or component?”
- tools: none
- evidence: none
- latency to agent speech: 4941 ms · step 41.6 s
  - ✔ vision: real panel, moving camera video

## barge_in  (session S-1001, agent ready in 15.0 s)

Agent audio recorded via Agora: barge_in.webm · mean -25.4 dB, peak 0.0 dB, None

### PASS `stop_open` · barge-in after 2 s of agent speech
- said: “Stop. Just tell me what is still open.”
- ASR heard: “Stop. | Just tell me what is still open.” (similarity 0.22)
- agent: “Three items are still open: 

1. There's a hypothesis that motor drive-end bearing wear could be contributing to the vibration and heat.
2. An open question remains about whether the vibration rises before or after the TEMP HIGH warning.
3. The coupling alignment and insert have not been checked yet.

How would you like to proceed with these?”
- tools: get_open_items[ok]
- evidence: none
- latency to agent speech: 5428 ms · step 55.5 s
  - ✔ agent was speaking when interrupted
  - ✔ answers the new request (open items)

## typed  (session S-1001, agent ready in 19.4 s)

Agent audio recorded via Agora: typed.webm · mean -27.0 dB, peak -3.3 dB, None

### PASS `bearing_stock` · blank:
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “Do we have the drive end bearing in stores?” (similarity 1.0)
- agent: “The drive end bearing, part number BRG-6316-C3, is currently out of stock in Stores A-14, with a lead time of 3 days. Would you like me to create a procurement request for this part?”
- tools: check_inventory[ok]
- evidence: none
- latency to agent speech: 3385 ms · step 55.1 s
  - ✔ typed message reached the agent and it checked inventory
