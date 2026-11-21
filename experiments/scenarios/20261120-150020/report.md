# Live scenario run 20261120-150020

**Checks passed: 22/41**


## vision  (session S-1001, agent ready in 18.8 s)

Agent audio recorded via Agora: vision.webm · mean -23.5 dB, peak -0.4 dB, None

### PASS `panel_read` · image:panel_alarm.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Let me check that.The display shows "A-17 DISCH TEMP HIGH" with a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. I'll record this observation now.”
- tools: none
- evidence: camera_model:Let me check that.The display shows "A-17 DISCH TEMP HIGH" w
- latency to agent speech: 1721 ms · step 27.2 s
  - ✔ vision: should read A-17/TEMP HIGH/108
  - ✔ camera observation saved to the evidence timeline — Let me check that.The display shows "A-17 DISCH TEMP HIGH" w

### PASS `panel_read` · image:panel_alarm.png {'blur': 5}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Give me a second.The display is blurry. Please hold your camera steady or move closer so I can get a clear reading.”
- tools: none
- evidence: camera_model:Give me a second.The display is blurry. Please hold your cam
- latency to agent speech: 1702 ms · step 19.6 s
  - ✔ vision: blurred: read it or say unclear
  - ✔ camera observation saved to the evidence timeline — Give me a second.The display is blurry. Please hold your cam

### PASS `panel_read` · image:panel_alarm.png {'bright': 0.3}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Okay, checking the system.The display shows "A-17 DISCH TEMP HIGH" with a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. I'll record this observation now.”
- tools: none
- evidence: camera_model:Okay, checking the system.The display shows "A-17 DISCH TEMP
- latency to agent speech: 1709 ms · step 27.7 s
  - ✔ vision: dim: read it or say too dark
  - ✔ camera observation saved to the evidence timeline — Okay, checking the system.The display shows "A-17 DISCH TEMP

### PASS `panel_read` · image:panel_alarm.png {'rotate': 22, 'zoom': 0.55}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “One moment, looking it up.The display shows "A-17 DISCH TEMP HIGH" with a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. I'll record this observation now.”
- tools: none
- evidence: camera_model:One moment, looking it up.The display shows "A-17 DISCH TEMP
- latency to agent speech: 1752 ms · step 28.4 s
  - ✔ vision: angled and far
  - ✔ camera observation saved to the evidence timeline — One moment, looking it up.The display shows "A-17 DISCH TEMP

### PASS `panel_read` · image:panel_alarm.png {'glare': True}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Pulling that up now.The display shows "A-17 DISCH TEMP HIGH" with a temperature of 108°C and a vibration reading of 7.4 mm/s. I'll record this observation as well.”
- tools: none
- evidence: camera_model:Pulling that up now.The display shows "A-17 DISCH TEMP HIGH"
- latency to agent speech: 1745 ms · step 27.8 s
  - ✔ vision: glare
  - ✔ camera observation saved to the evidence timeline — Pulling that up now.The display shows "A-17 DISCH TEMP HIGH"

### PASS `panel_read` · image:panel_normal.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Okay, checking the system.The display shows "NO ACTIVE ALARM" with a discharge temperature of 96°C and a vibration reading of 2.6 mm/s. I'll record this observation now.”
- tools: none
- evidence: camera_model:Okay, checking the system.The display shows "NO ACTIVE ALARM
- latency to agent speech: 2964 ms · step 29.2 s
  - ✔ vision: normal panel: must NOT report A-17
  - ✔ camera observation saved to the evidence timeline — Okay, checking the system.The display shows "NO ACTIVE ALARM

### FAIL `panel_read` · image:panel_a22.png
- said: “What does the panel display show right now?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools unreachable from Agora (tunnel down)
- latency to agent speech: None ms · step 55.0 s
  - ✘ vision: should read A-22 / 9.2 (not the previous frame)
  - ✘ camera observation saved to the evidence timeline

### FAIL `alarm_code` · blank:
- said: “Read me the alarm code on the display.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.0 s
  - ✘ vision: blank camera: must not invent a code
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_real_westinghouse.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “” (similarity 0.0)
- agent: “SHIFTTRACE is live on Compressor C-204. Kavya, ask me what happened on the previous shift, or point your camera at the panel.”
- tools: none
- evidence: none
- latency to agent speech: None ms · step 23.7 s
  - ✔ vision: real photo (Flickr): old compressor
  - ✘ camera observation saved to the evidence timeline

### FAIL `alarm_code` · image:img_real_panel_1.jpg
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “One moment, looking it up.It seems I'm unable to see any specific alarm codes in the current view. Please adjust the camera closer to any display or alarm panel that might have the alarm codes visible.”
- tools: none
- evidence: none
- latency to agent speech: 2615 ms · step 30.9 s
  - ✔ vision: real industrial panel: must not carry over A-17 from earlier frames
  - ✘ camera observation saved to the evidence timeline

### PASS `what_machine` · image:img_real_gauge.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Let me check that.You're looking at a set of pressure and vacuum gauges. These typically measure the pressure or vacuum levels in a system,”
- tools: none
- evidence: camera_model:Let me check that.You're looking at a set of pressure and va
- latency to agent speech: 9901 ms · step 33.5 s
  - ✔ vision: real photo: pressure gauge
  - ✔ camera observation saved to the evidence timeline — Let me check that.You're looking at a set of pressure and va

### PASS `what_machine` · video:vid_real_panel_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Let me check that.This is likely a schematic diagram for a control system, possibly for a process plant or machinery. It shows various components, including sensors, valves, and flow paths, which indicate how different equipment interacts within the system. Would you like to explore any specific part of this diagram?”
- tools: none
- evidence: camera_model:Let me check that.This is likely a schematic diagram for a c
- latency to agent speech: 3933 ms · step 34.7 s
  - ✔ vision: real panel, moving camera video
  - ✔ camera observation saved to the evidence timeline — Let me check that.This is likely a schematic diagram for a c

## core  (session S-1001, agent ready in 24.6 s)

Agent audio recorded via Agora: core.webm · mean -25.3 dB, peak -0.1 dB, None

### FAIL `prev_shift` · image:panel_alarm.png
- said: “What happened to this compressor on the previous shift?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: get_previous_handoff[ok], get_asset_history[ok]
- evidence: none
- latency to agent speech: None ms · step 56.9 s
  - ✔ retrieved history/handoff
  - ✘ mentions sensor or vibration

### PASS `look_panel` · image:panel_alarm.png
- said: “I'm pointing the camera at the panel now. What do you see?”
- ASR heard: “I'm pointing the camera at the panel now. What do you see?” (similarity 1.0)
- agent: “Pulling that up now.” / “I've recorded the observation: the TEMP HIGH lamp is lit, showing 108°C on A-17 and the vibration is at 7.4 mm/s. This ties in with existing open questions regarding possible causes. Would you like to address any of the open items or take an action?”
- tools: record_observation[ok]
- evidence: camera_model:TEMP HIGH lamp lit; A-17 DISCHARGE TEMP shows 108 °C; vibrat
- latency to agent speech: 2941 ms · step 47.7 s
  - ✔ reads alarm from camera
  - ✔ records visual evidence

### FAIL `shook_first` · image:panel_alarm.png
- said: “It started shaking first, and then the temperature warning came on.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools unreachable from Agora (tunnel down)
- latency to agent speech: None ms · step 55.1 s
  - ✘ records technician report
  - ✘ closes the 'before or after' open loop — soft

### FAIL `manual_a17` · image:panel_alarm.png
- said: “What does the manual say about the A seventeen alarm coming back after a sensor swap?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.8 s
  - ✘ searched manual
  - ✘ cites sensor/section

### FAIL `bearing_stock` · image:panel_alarm.png
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools reachable again
- latency to agent speech: None ms · step 55.6 s
  - ✘ checked inventory
  - ✘ reports out of stock

### FAIL `raise_pr` · image:panel_alarm.png
- said: “Raise a procurement request for one drive end bearing.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: cmms:Maintenance tools unreachable from Agora (tunnel down)
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
- latency to agent speech: None ms · step 55.6 s
  - ✘ PR submitted in DB
  - ✘ agent states expected date

### FAIL `wo_hold` · image:panel_alarm.png
- said: “Put the work order on hold for parts.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.6 s
  - ✘ WO set WAITING_PARTS — IN_PROGRESS

### FAIL `handoff` · image:panel_alarm.png
- said: “Prepare the handoff for the next shift.”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.0 s
  - ✘ handoff created
