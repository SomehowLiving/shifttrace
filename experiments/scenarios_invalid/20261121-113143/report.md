# Live scenario run 20261121-113143

**Checks passed: 32/45**


## vision_dataset  (session S-1001, agent ready in 21.7 s)

Agent audio recorded via Agora: vision_dataset.webm · mean -21.0 dB, peak -0.5 dB, None

### FAIL `what_machine` · image:img_ds_gauge_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge temperature of 108 degrees Celsius and a vibration measurement of 7.4 mm/s. The "TEMP HIGH" alarm is lit, indicating a potentially critical issue. Would you like to check the previous handoff or troubleshoot the fault?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1946 ms · step 38.0 s
  - ✘ describes it (analogue pressure gauge; needle reading may be estimated, not exact) — You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge temperature of 108
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_gauge_3.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Give me a second.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a high discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s. Would you like to proceed with troubleshooting the fault?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1998 ms · step 34.8 s
  - ✘ describes it (locomotive cab with several analogue gauges and valves; readings not legible) — Give me a second.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a high di
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_conveyor_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Let me check that.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a discharge temperature of 108 degrees Celsius and a vibration measurement of 7.4 mm/s, with the "TEMP HIGH" alarm lit. Would you like to proceed with troubleshooting the fault?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 2023 ms · step 36.6 s
  - ✘ describes it (food factory conveyor carrying product past a machine) — Let me check that.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a discha
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_conveyor_3.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Pulling that up now.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s, with the "TEMP HIGH" alarm lit. Would you like to check the previous shift's notes or begin troubleshooting?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1839 ms · step 37.6 s
  - ✘ describes it (vehicle assembly line with overhead conveyor) — Pulling that up now.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharg
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_warehouse_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Okay, checking the system.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge temperature of 108 degrees Celsius and a vibration measurement of 7.4 mm/s. The "TEMP HIGH" alarm is active, suggesting there may be an issue to address. Would you like to check the previous handoff or start troubleshooting?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1655 ms · step 41.1 s
  - ✘ describes it (warehouse racking with pallets or cartons) — Okay, checking the system.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a di
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_warehouse_2.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “One moment, looking it up.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s, with the "TEMP HIGH" alarm active. Do you want to check the previous shift's notes or begin troubleshooting?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1886 ms · step 39.8 s
  - ✘ describes it (warehouse racking with pallets or cartons) — One moment, looking it up.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates 
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_warehouse_3.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Give me a second.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a high discharge temperature of 108 degrees Celsius and a vibration measurement of 7.4 mm/s, with the "TEMP HIGH" alarm lit. Would you like to check the history or start troubleshooting the fault?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1782 ms · step 39.1 s
  - ✘ describes it (warehouse racking with pallets or cartons) — Give me a second.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a high discha
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_forklift_2.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “One moment, looking it up.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s, with the "TEMP HIGH" alarm active. Would you like to check the previous handoff or start troubleshooting the current fault?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1772 ms · step 38.6 s
  - ✘ describes it (warehouse racking full of cartons (no forklift visible)) — One moment, looking it up.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a di
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_hvac_2.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Pulling that up now.You are looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s, with the "TEMP HIGH" alarm currently active. Would you like to proceed with troubleshooting or check the previous handoff?”
- tools: none
- evidence: camera_model:You are looking at a Kestrel KS-75 Rotary Screw Compressor, 
- latency to agent speech: 1817 ms · step 39.8 s
  - ✘ describes it (supply air duct and vibration isolators in a plant room) — Pulling that up now.You are looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a dis
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_motor_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Let me check that.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s, along with a "TEMP HIGH" alarm indicating a potential issue. Would you like to check the previous handoff or start troubleshooting?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1879 ms · step 38.3 s
  - ✘ describes it (electric drive motor in a vehicle chassis) — Let me check that.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge 
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### PASS `what_machine` · image:img_ds_compressor_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Okay, checking the system.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s, with a "TEMP HIGH" alarm active. Would you like to check the previous shift's notes or start troubleshooting?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1729 ms · step 40.2 s
  - ✔ describes it (outdoor air compressor driven by a car engine) — Okay, checking the system.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates 
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### PASS `what_machine` · image:img_ds_display_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Okay, checking the system.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s, with the "TEMP HIGH" alarm lit. Would you like to check on the previous shift's notes or proceed with troubleshooting?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor,
- latency to agent speech: 1778 ms · step 39.9 s
  - ✔ describes it (room thermostat display reading 22.5 C) — Okay, checking the system.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a di
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · video:vid_ds_conveyor_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “One moment, looking it up.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge temperature of 108 degrees Celsius and a vibration measurement of 7.4 mm/s, with the "TEMP HIGH" alarm lit. Would you like to review the previous shift's notes or start troubleshooting?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1722 ms · step 43.0 s
  - ✘ describes it (hand-held pan along a factory conveyor) — One moment, looking it up.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a di
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · video:vid_ds_warehouse_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Give me a second.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s, with the "TEMP HIGH" alarm active. Would you like to check the previous shift's notes or start troubleshooting the issue?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 1738 ms · step 41.0 s
  - ✘ describes it (hand-held walk past warehouse racking) — Give me a second.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display shows a discharge t
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · video:vid_ds_gauge_zoom.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Pulling that up now.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a discharge temperature of 108 degrees Celsius and a vibration level of 7.4 mm/s, with the "TEMP HIGH" alarm activated. Would you like to check the previous shift's notes or proceed with troubleshooting?”
- tools: none
- evidence: camera_model:You're looking at a Kestrel KS-75 Rotary Screw Compressor, m
- latency to agent speech: 2272 ms · step 42.8 s
  - ✘ describes it (hand-held zoom onto pressure gauges, slight shake) — Pulling that up now.You're looking at a Kestrel KS-75 Rotary Screw Compressor, model C-204. The display indicates a disc
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline
