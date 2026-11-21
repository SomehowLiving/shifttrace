# Live scenario run 20261121-022144

**Checks passed: 24/24**


## vision  (session S-1001, agent ready in 19.0 s)

Agent audio recorded via Agora: vision.webm · mean -21.1 dB, peak -1.0 dB, None

### PASS `panel_read` · image:panel_alarm.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “One moment, looking it up.” / “The panel shows a discharge temperature of 108 °C, which is above the 105 °C limit, and the TEMP HIGH lamp is lit. It also displays a vibration reading of 7.4 mm/s, exceeding the 7.1 mm/s limit. 

Both values indicate out-of-limit conditions. Would you like to check any particular aspect or proceed with troubleshooting?”
- tools: record_reading[ok], record_observation[ok], record_reading[ok]
- evidence: camera_model:DE vibration: 7.4 mm/s (out of limit), agent_inference:DE vibration 7.4 mm/s out of limit: follow up, camera_model:TEMP HIGH lamp is lit, displaying 108 C and 7.4 mm/s, camera_model:discharge temperature: 108 °C (out of limit), agent_inference:discharge temperature 108 °C out of limit: follow up
- latency to agent speech: 1714 ms · step 44.9 s
  - ✔ vision: should read A-17/TEMP HIGH/108
  - ✔ camera observation saved to the evidence timeline — DE vibration: 7.4 mm/s (out of limit); TEMP HIGH lamp is lit, displaying 108 C and 7.4 mm/s; discharge temperature: 108 °C (out of limit)

### PASS `panel_read` · image:panel_alarm.png {'blur': 5}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel show right now?” (similarity 0.93)
- agent: “Give me a second.The panel appears blurred. Please hold it steady or move closer so I can check the readings accurately.”
- tools: none
- evidence: camera_model:The panel appears blurred. Please hold it steady or move clo
- latency to agent speech: 1633 ms · step 19.9 s
  - ✔ vision: blurred: read it or say unclear
  - ✔ camera observation saved to the evidence timeline — The panel appears blurred. Please hold it steady or move clo

### PASS `panel_read` · image:panel_alarm.png {'bright': 0.3}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Pulling that up now.The panel shows a discharge temperature of 108 °C and a vibration reading of 7.4 mm/s. The TEMP HIGH lamp is still lit. Would you like to investigate a specific issue?”
- tools: none
- evidence: camera_model:The panel shows a discharge temperature of 108 °C and a vibr
- latency to agent speech: 1682 ms · step 28.7 s
  - ✔ vision: dim: read it or say too dark
  - ✔ camera observation saved to the evidence timeline — The panel shows a discharge temperature of 108 °C and a vibr

### PASS `panel_read` · image:panel_alarm.png {'rotate': 22, 'zoom': 0.55}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Okay, checking the system.The panel shows a discharge temperature of 108 °C and a vibration reading of 7.4 mm/s. The TEMP HIGH lamp is lit. Would you like to troubleshoot a specific issue now?”
- tools: none
- evidence: camera_model:The panel shows a discharge temperature of 108 °C and a vibr
- latency to agent speech: 1696 ms · step 28.3 s
  - ✔ vision: angled and far
  - ✔ camera observation saved to the evidence timeline — The panel shows a discharge temperature of 108 °C and a vibr

### PASS `panel_read` · image:panel_alarm.png {'glare': True}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Let me check that.The panel displays a discharge temperature of 108 °C and a vibration reading of 7.4 mm/s, with the TEMP HIGH lamp lit. Would you like to take any specific troubleshooting steps?”
- tools: none
- evidence: camera_model:The panel displays a discharge temperature of 108 °C and a v
- latency to agent speech: 1678 ms · step 28.8 s
  - ✔ vision: glare
  - ✔ camera observation saved to the evidence timeline — The panel displays a discharge temperature of 108 °C and a v

### PASS `panel_read` · image:panel_normal.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Give me a second.The panel now shows no active alarm, with a discharge temperature of 96 °C and a vibration reading of 2.6 mm/s. How would you like to proceed with troubleshooting or further checks?”
- tools: none
- evidence: camera_model:The panel now shows no active alarm, with a discharge temper
- latency to agent speech: 1662 ms · step 27.4 s
  - ✔ vision: normal panel: must NOT report A-17
  - ✔ camera observation saved to the evidence timeline — The panel now shows no active alarm, with a discharge temper

### PASS `panel_read` · image:panel_a22.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Pulling that up now.Let me pull that up for you. The panel shows an alarm A-22 for vibration high, with a discharge temperature of 97 °C and a vibration reading of 9.2 mm/s. What would you like to do next?”
- tools: none
- evidence: camera_model:Let me pull that up for you. The panel shows an alarm A-22 f
- latency to agent speech: 1646 ms · step 30.2 s
  - ✔ vision: should read A-22 / 9.2 (not the previous frame)
  - ✔ camera observation saved to the evidence timeline — Let me pull that up for you. The panel shows an alarm A-22 f

### PASS `alarm_code` · blank:
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “Let me check that.I can't see the display right now. Please hold it steady so I can check the alarm code properly.”
- tools: none
- evidence: camera_model:I can't see the display right now. Please hold it steady so 
- latency to agent speech: 1720 ms · step 18.9 s
  - ✔ vision: blank camera: must not invent a code
  - ✔ camera observation saved to the evidence timeline — I can't see the display right now. Please hold it steady so 

### PASS `what_machine` · image:img_real_westinghouse.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Okay, checking the system.You're looking at a diagram of a Westinghouse air compressor. It illustrates the components and connections involved in its operation. Would you like to discuss a specific part or ask about its functionality?”
- tools: none
- evidence: camera_model:You're looking at a diagram of a Westinghouse air compressor
- latency to agent speech: 1635 ms · step 27.2 s
  - ✔ vision: real photo (Flickr): old compressor
  - ✔ camera observation saved to the evidence timeline — You're looking at a diagram of a Westinghouse air compressor

### PASS `alarm_code` · image:img_real_panel_1.jpg
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “One moment, looking it up.I can't see an alarm code in this image. It appears to show a control panel with various gauges and controls for different equipment. If you have a specific display or alarm panel to check, please point to it.”
- tools: none
- evidence: camera_model:I can't see an alarm code in this image. It appears to show 
- latency to agent speech: 1701 ms · step 28.5 s
  - ✔ vision: real industrial panel: must not carry over A-17 from earlier frames
  - ✔ camera observation saved to the evidence timeline — I can't see an alarm code in this image. It appears to show 

### PASS `what_machine` · image:img_real_gauge.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Pulling that up now.You're looking at pressure gauges. The left one measures vacuum, the middle one also indicates vacuum, and the right one measures oil pressure. Would you like to know more about how they function or their applications?”
- tools: none
- evidence: camera_model:You're looking at pressure gauges. The left one measures vac
- latency to agent speech: 1629 ms · step 29.2 s
  - ✔ vision: real photo: pressure gauge
  - ✔ camera observation saved to the evidence timeline — You're looking at pressure gauges. The left one measures vac

### PASS `what_machine` · video:vid_real_panel_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Give me a second.You're looking at a control panel schematic for a process or manufacturing system, likely involving boilers, condensate systems, and extraction processes. It shows the flow of materials and connections among various components for the operation of the system. Would you like to dive deeper into a specific section or ask about its functions?”
- tools: none
- evidence: camera_model:You're looking at a control panel schematic for a process or
- latency to agent speech: 1618 ms · step 39.9 s
  - ✔ vision: real panel, moving camera video
  - ✔ camera observation saved to the evidence timeline — You're looking at a control panel schematic for a process or
