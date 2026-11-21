# Live scenario run 20261120-135910

**Checks passed: 11/17**


## recovery: ERROR

`ReadTimeout: timed out`

## core  (session S-1001, agent ready in 19.9 s)

Agent audio recorded via Agora: core.webm · mean -22.6 dB, peak -1.2 dB, None

### PASS `prev_shift` · image:panel_alarm.png
- said: “What happened to this compressor on the previous shift?”
- ASR heard: “What happened to this compressor on the previous shift?” (similarity 1.0)
- agent: “On the previous shift, technician Anil Mehta replaced the TS-2 temperature sensor after the A-17 warning occurred. However, the warning returned about 40 minutes later, ruling out the sensor as the cause. There are suspicions that the drive-end bearing may be worn, and vibration was recorded at 7.4 mm/s, which is in the alarm zone. Would you like to check the open work orders next?”
- tools: get_previous_handoff[ok]
- evidence: none
- latency to agent speech: 4054 ms · step 55.6 s
  - ✔ retrieved history/handoff
  - ✔ mentions sensor or vibration

### PASS `look_panel` · image:panel_alarm.png
- said: “I'm pointing the camera at the panel now. What do you see?”
- ASR heard: “I'm pointing the camera at the panel now. | What do you see?” (similarity 0.82)
- agent: “I see that the TEMP HIGH lamp is lit, with the discharge temperature reading at 108 °C and vibration at 7.4 mm/s. I've recorded this observation. However, it seems that the related open loop could not be closed with this evidence. Do you want to check the inventory for parts next?”
- tools: record_observation[ok], update_open_item[error]
- evidence: camera_model:TEMP HIGH lamp lit; A-17 discharge temperature at 108 °C; vi
- latency to agent speech: 5555 ms · step 55.6 s
  - ✔ reads alarm from camera
  - ✔ records visual evidence

### FAIL `shook_first` · image:panel_alarm.png
- said: “It started shaking first, and then the temperature warning came on.”
- ASR heard: “It started shaking first, and then the temperature warning came on.” (similarity 1.0)
- agent: “I've recorded your observation that the compressor started shaking before the temperature warning. This information is important for assessing potential issues, including bearing wear. Would you like to check the inventory for the bearing now?”
- tools: record_observation[ok]
- evidence: technician:Shaking occurred before the temperature warning.
- latency to agent speech: 4933 ms · step 55.1 s
  - ✔ records technician report
  - ✘ closes the 'before or after' open loop — soft

### FAIL `manual_a17` · image:panel_alarm.png
- said: “What does the manual say about the A seventeen alarm coming back after a sensor swap?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools unreachable from Agora (tunnel down)
- latency to agent speech: 12237 ms · step 55.6 s
  - ✘ searched manual
  - ✘ cites sensor/section

### PASS `bearing_stock` · image:panel_alarm.png
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “” (similarity 0.0)
- agent: “The BRG-6316-C3 bearing is currently out of stock, with zero available in Stores A-14. It has a lead time of 3 days for procurement. Would you like me to create a procurement request for it?”
- tools: check_inventory[ok]
- evidence: cmms:Maintenance tools reachable again
- latency to agent speech: 1632 ms · step 55.5 s
  - ✔ checked inventory
  - ✔ reports out of stock

### PASS `raise_pr` · image:panel_alarm.png
- said: “Raise a procurement request for one drive end bearing.”
- ASR heard: “Drive and bearing.” (similarity 0.33)
- agent: “I’ve drafted a procurement request for one Bearing 6316-C3, linked to work order WO-1187. The supplier is Southfield Bearings, with a lead time of 3 days. Shall I submit this request?”
- tools: create_procurement_request[ok]
- evidence: tool_result:Procurement draft PR-2001 created: 1 x BRG-6316-C3 (awaiting
- latency to agent speech: 6756 ms · step 55.1 s
  - ✔ drafted PR
  - ✔ did NOT submit without a yes
  - ✔ asks for confirmation

### FAIL `yes_submit` · image:panel_alarm.png
- said: “Yes, submit it.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools unreachable from Agora (tunnel down)
- latency to agent speech: 2326 ms · step 55.6 s
  - ✘ PR submitted in DB — PR-2001=PENDING_APPROVAL
  - ✘ agent states expected date

### PASS `wo_hold` · image:panel_alarm.png
- said: “Put the work order on hold for parts.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: update_work_order[ok]
- evidence: tool_result:WO-1187 IN_PROGRESS -> WAITING_PARTS
- latency to agent speech: 5820 ms · step 55.1 s
  - ✔ WO set WAITING_PARTS — WAITING_PARTS

### FAIL `handoff` · image:panel_alarm.png
- said: “Prepare the handoff for the next shift.”
- ASR heard: “Prepare the handoff for the next shift.” (similarity 1.0)
- agent: “It seems there was an issue processing the handoff. Let me try that again. One moment.” / “It appears I'm unable to create the handoff at this moment. You may need to document the current status of Compressor C-204 manually. You’ve noted the high discharge temperature of 108 °C, the vibration at 7.4 mm/s, and the work order is on hold for parts. Would you like to do anything else?” / “I'm still encountering issues with creating the handoff. Let's summarize the key points before the next shift:

The Compressor C-204 has a discharge temperature of 108 °C and a vibration reading of 7.4 mm/s. The work order WO-1187 is currently on hold for procurement of Bearing 6316-C3. 

If there's anything specific you want to add or adjust, let me know!”
- tools: none
- evidence: cmms:Maintenance tools reachable again
- latency to agent speech: 18555 ms · step 55.1 s
  - ✘ handoff created
