# Live scenario run 20261120-001548

**Checks passed: 12/12**


## vision  (session S-1001, agent ready in 17.8 s)

Agent audio recorded via Agora: vision.webm · mean -22.1 dB, peak -0.2 dB, None

### PASS `panel_read` · image:panel_alarm.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The display shows "A-17 DISCH TEMP HIGH" with a discharge temperature of 108°C. The vibration reading is 7.4 mm/s. I will record this observation now.”
- tools: none
- evidence: none
- latency to agent speech: 1926 ms · step 23.4 s
  - ✔ vision: should read A-17/TEMP HIGH/108

### PASS `panel_read` · image:panel_alarm.png {'blur': 5}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The display is blurry, and I can't clearly see the readings. Please hold the camera steady or move closer for a better view.”
- tools: none
- evidence: none
- latency to agent speech: 2656 ms · step 18.4 s
  - ✔ vision: blurred: read it or say unclear

### PASS `panel_read` · image:panel_alarm.png {'bright': 0.3}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The display shows "A-17 DISCH TEMP HIGH" with a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. I'll record this observation now.”
- tools: none
- evidence: none
- latency to agent speech: 3371 ms · step 24.6 s
  - ✔ vision: dim: read it or say too dark

### PASS `panel_read` · image:panel_alarm.png {'rotate': 22, 'zoom': 0.55}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The display shows "A-17 DISCH TEMP HIGH" with a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. I will record this observation.”
- tools: none
- evidence: none
- latency to agent speech: 3159 ms · step 25.0 s
  - ✔ vision: angled and far

### PASS `panel_read` · image:panel_alarm.png {'glare': True}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The display shows "A-17 DISCH TEMP HIGH" with a discharge temperature of 108°C and a vibration reading of 7.4 mm/s. I will record this observation now.”
- tools: none
- evidence: none
- latency to agent speech: 4130 ms · step 27.1 s
  - ✔ vision: glare

### PASS `panel_read` · image:panel_normal.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The display shows "NO ACTIVE ALARM" with a discharge temperature of 96°C and a vibration reading of 2.6 mm/s. I'll record this observation now.”
- tools: none
- evidence: none
- latency to agent speech: 3815 ms · step 24.5 s
  - ✔ vision: normal panel: must NOT report A-17

### PASS `panel_read` · image:panel_a22.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The display shows "A-22 VIBRATION HIGH" with a discharge temperature of 97°C and a vibration reading of 9.2 mm/s. I'll record this observation now.”
- tools: none
- evidence: none
- latency to agent speech: 4762 ms · step 25.9 s
  - ✔ vision: should read A-22 / 9.2 (not the previous frame)

### PASS `alarm_code` · blank:
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “I can't see the display right now. Please adjust the camera for better visibility.”
- tools: none
- evidence: none
- latency to agent speech: 4333 ms · step 16.4 s
  - ✔ vision: blank camera: must not invent a code

### PASS `what_machine` · image:img_real_westinghouse.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a diagram of a Westinghouse air compressor. It illustrates various components and their connections, such as valves and gauges, related to the operation of the compressor.”
- tools: none
- evidence: none
- latency to agent speech: 4297 ms · step 23.4 s
  - ✔ vision: real photo (Flickr): old compressor

### PASS `alarm_code` · image:img_real_panel_1.jpg
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “I can't see the alarm code from the display. Please point closer to the relevant area for visibility.”
- tools: none
- evidence: none
- latency to agent speech: 4177 ms · step 17.1 s
  - ✔ vision: real industrial panel: must not carry over A-17 from earlier frames

### PASS `what_machine` · image:img_real_gauge.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a set of gauges, specifically a vacuum gauge and an oil pressure gauge. These are used for measuring the pressure and vacuum in various systems, likely in industrial or mechanical applications.”
- tools: none
- evidence: none
- latency to agent speech: 5153 ms · step 25.9 s
  - ✔ vision: real photo: pressure gauge

### PASS `what_machine` · video:vid_real_panel_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a control panel for a steam system or thermal power plant. It shows various components such as boilers, condensers, and pumps, along with their connections and operational parameters for monitoring and control.”
- tools: none
- evidence: none
- latency to agent speech: 6251 ms · step 27.8 s
  - ✔ vision: real panel, moving camera video
