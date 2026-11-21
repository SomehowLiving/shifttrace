# Live scenario run 20261120-000846

**Checks passed: 11/12**


## vision  (session S-1001, agent ready in 23.4 s)

Agent audio recorded via Agora: vision.webm · mean -22.2 dB, peak -0.0 dB, None

### PASS `panel_read` · image:panel_alarm.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel do? Display show right now?” (similarity 0.94)
- agent: “The panel shows a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. The "TEMP HIGH" lamp is lit, indicating a high temperature condition. Would you like to check the manual for possible causes?”
- tools: none
- evidence: none
- latency to agent speech: 11358 ms · step 28.7 s
  - ✔ vision: should read A-17/TEMP HIGH/108

### PASS `panel_read` · image:panel_alarm.png {'blur': 5}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The panel currently displays a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. The "TEMP HIGH" lamp is still illuminated. Please hold the camera steady for clearer details if needed.”
- tools: none
- evidence: none
- latency to agent speech: 6704 ms · step 27.9 s
  - ✔ vision: blurred: read it or say unclear

### PASS `panel_read` · image:panel_alarm.png {'bright': 0.3}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The panel shows a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. The "TEMP HIGH" lamp remains lit.”
- tools: none
- evidence: none
- latency to agent speech: 8297 ms · step 23.2 s
  - ✔ vision: dim: read it or say too dark

### PASS `panel_read` · image:panel_alarm.png {'rotate': 22, 'zoom': 0.55}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The panel displays a discharge temperature of 108°C and a vibration reading of 7.4 mm/s, with the "TEMP HIGH" lamp still lit. Would you like to troubleshoot further?”
- tools: none
- evidence: none
- latency to agent speech: 3003 ms · step 24.5 s
  - ✔ vision: angled and far

### PASS `panel_read` · image:panel_alarm.png {'glare': True}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The panel shows a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. The "TEMP HIGH" lamp is still illuminated. What action would you like to take next?”
- tools: none
- evidence: none
- latency to agent speech: 2991 ms · step 26.1 s
  - ✔ vision: glare

### PASS `panel_read` · image:panel_normal.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The panel now shows "NO ACTIVE ALARM," a discharge temperature of 96°C, and a vibration reading of 2.6 mm/s. Would you like to log this observation or proceed with another action?”
- tools: none
- evidence: none
- latency to agent speech: 4216 ms · step 28.7 s
  - ✔ vision: normal panel: must NOT report A-17

### PASS `panel_read` · image:panel_a22.png
- said: “What does the panel display show right now?”
- ASR heard: “Right now,” (similarity 0.4)
- agent: “The panel displays "NO ACTIVE ALARM," a discharge temperature of 96°C, and a vibration reading of 2.6 mm/s. What would you like to do next?”
- tools: none
- evidence: none
- latency to agent speech: 5847 ms · step 26.7 s
  - ✔ vision: should read A-22 vibration

### FAIL `alarm_code` · blank:
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “There is currently no active alarm displayed on the panel. Would you like to check the manual for alarm codes?”
- tools: none
- evidence: none
- latency to agent speech: 4492 ms · step 18.0 s
  - ✘ vision: blank camera: must not invent a code

### PASS `what_machine` · image:img_real_westinghouse.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a schematic diagram of a Westinghouse air compressor. It shows components like the boiler, valves, and the air pump connections. Would you like to know more about specific parts or how they function?”
- tools: none
- evidence: none
- latency to agent speech: 3586 ms · step 26.1 s
  - ✔ vision: real photo (Flickr): old compressor

### PASS `alarm_code` · image:img_real_panel_1.jpg
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “I can't see an alarm code displayed in this view. Would you like to adjust the camera or check a specific area?”
- tools: none
- evidence: none
- latency to agent speech: 4364 ms · step 18.2 s
  - ✔ vision: real industrial panel: must not carry over A-17 from earlier frames

### PASS `what_machine` · image:img_real_gauge.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a set of pressure and vacuum gauges. The left and middle ones are vacuum gauges, while the right one measures oil pressure. Would you like to know how to use them or their specifications?”
- tools: none
- evidence: none
- latency to agent speech: 5560 ms · step 26.6 s
  - ✔ vision: real photo: pressure gauge

### PASS `what_machine` · video:vid_real_panel_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a control panel for electrical equipment, likely related to power generation or distribution. It includes various gauges, switches, and indicators for monitoring system conditions. Would you like information on specific components?”
- tools: none
- evidence: none
- latency to agent speech: 5417 ms · step 28.6 s
  - ✔ vision: real panel, moving camera video
