# Live scenario run 20261121-114453

**Checks passed: 31/45**


## vision_dataset  (session S-1001, agent ready in 19.0 s)

Agent audio recorded via Agora: vision_dataset.webm · mean -20.6 dB, peak -0.1 dB, None

### PASS `what_machine` · image:img_ds_gauge_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “It looks like you're looking at a pressure gauge. The gauge shows pressure measurements in kilograms per square centimeter (kg/cm²). Would you like to check a specific reading or observation?”
- tools: none
- evidence: camera_model:It looks like you're looking at a pressure gauge. The gauge 
- latency to agent speech: 1616 ms · step 24.4 s
  - ✔ describes it (analogue pressure gauge; needle reading may be estimated, not exact) — It looks like you're looking at a pressure gauge. The gauge shows pressure measurements in kilograms per square centimet
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_gauge_3.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “One moment, looking it up.It appears you're looking at the boiler and associated piping of a steam locomotive. This equipment is used for generating steam to power the locomotive. Would you like to check for any specific readings or observations related to this?”
- tools: none
- evidence: camera_model:It appears you're looking at the boiler and associated pipin
- latency to agent speech: 1838 ms · step 28.9 s
  - ✘ describes it (locomotive cab with several analogue gauges and valves; readings not legible) — One moment, looking it up.It appears you're looking at the boiler and associated piping of a steam locomotive. This equi
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### PASS `what_machine` · image:img_ds_conveyor_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Pulling that up now.You're looking at a chocolate depositing machine. It appears to be used for shaping and depositing chocolate in a factory setting. Do you need any specific readings or checks on this equipment?”
- tools: none
- evidence: camera_model:You're looking at a chocolate depositing machine. It appears
- latency to agent speech: 1619 ms · step 24.4 s
  - ✔ describes it (food factory conveyor carrying product past a machine) — Pulling that up now.You're looking at a chocolate depositing machine. It appears to be used for shaping and depositing c
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### PASS `what_machine` · image:img_ds_conveyor_3.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Let me check that.You're looking at an automotive assembly line. It shows the process of building cars, with components being assembled together. Would you like to focus on any specific aspect or equipment related to this setup?”
- tools: none
- evidence: camera_model:You're looking at an automotive assembly line. It shows the 
- latency to agent speech: 1678 ms · step 27.4 s
  - ✔ describes it (vehicle assembly line with overhead conveyor) — Let me check that.You're looking at an automotive assembly line. It shows the process of building cars, with components 
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_warehouse_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Okay, checking the system.It looks like you are viewing a storage facility or warehouse. The shelves are stacked with boxes, possibly containing supplies or goods from organizations like USAID. Would you like to focus on something specific in this context?”
- tools: none
- evidence: none
- latency to agent speech: 1805 ms · step 28.0 s
  - ✔ describes it (warehouse racking with pallets or cartons) — Okay, checking the system.It looks like you are viewing a storage facility or warehouse. The shelves are stacked with bo
  - ✔ does not invent an alarm code
  - ✘ camera observation saved to the evidence timeline

### PASS `what_machine` · image:img_ds_warehouse_2.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Give me a second.It seems you are looking at another section of a warehouse or storage facility. The shelves are filled with boxes labeled USAID, indicating supplies or humanitarian aid. Would you like to verify any specific details or perform a check related to this setup?”
- tools: none
- evidence: camera_model:It seems you are looking at another section of a warehouse o
- latency to agent speech: 1631 ms · step 32.2 s
  - ✔ describes it (warehouse racking with pallets or cartons) — Give me a second.It seems you are looking at another section of a warehouse or storage facility. The shelves are filled 
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_warehouse_3.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Okay, checking the system.Let me check that for you.It looks like you are viewing a warehouse or distribution center with a forklift in use. The forklift is being operated to move pallets labeled with USAID, likely for logistics or distribution purposes. Do you need any specific details or tasks related to this setup?”
- tools: none
- evidence: none
- latency to agent speech: 1644 ms · step 34.7 s
  - ✔ describes it (warehouse racking with pallets or cartons) — Okay, checking the system.Let me check that for you.It looks like you are viewing a warehouse or distribution center wit
  - ✔ does not invent an alarm code
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_forklift_2.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “One moment, looking it up.Let me check.You're looking at a warehouse or distribution center setup, featuring high shelves stacked with various pallets. The pallets are wrapped and labeled, indicating stored goods or supplies. Would you like to gather any specific information or make any checks related to this equipment?”
- tools: none
- evidence: none
- latency to agent speech: 1626 ms · step 34.9 s
  - ✔ describes it (warehouse racking full of cartons (no forklift visible)) — One moment, looking it up.Let me check.You're looking at a warehouse or distribution center setup, featuring high shelve
  - ✔ does not invent an alarm code
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_hvac_2.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Give me a second.Let me check that for you.It looks like you're viewing HVAC ductwork and an air handling unit. This equipment is used for heating, ventilation, and air conditioning within a building. Would you like to investigate anything specific related to this setup?”
- tools: none
- evidence: none
- latency to agent speech: 1648 ms · step 31.0 s
  - ✔ describes it (supply air duct and vibration isolators in a plant room) — Give me a second.Let me check that for you.It looks like you're viewing HVAC ductwork and an air handling unit. This equ
  - ✔ does not invent an alarm code
  - ✘ camera observation saved to the evidence timeline

### PASS `what_machine` · image:img_ds_motor_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Pulling that up now.Let me check that for you.You're looking at the engine compartment of an electric or hybrid vehicle. It shows the electric motor, cooling systems, and associated components. Do you need to explore any specific aspects or details related to this equipment?”
- tools: none
- evidence: camera_model:Let me check that for you.You're looking at the engine compa
- latency to agent speech: 1643 ms · step 31.0 s
  - ✔ describes it (electric drive motor in a vehicle chassis) — Pulling that up now.Let me check that for you.You're looking at the engine compartment of an electric or hybrid vehicle.
  - ✔ does not invent an alarm code
  - ✔ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_compressor_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Let me check that.Let me check that for you.It looks like you're looking at a small, portable gasoline engine, likely used for various applications like irrigation or powering tools. It's part of a makeshift setup, often seen in informal settings. Would you like to explore any specific details or tasks related to this equipment?”
- tools: none
- evidence: none
- latency to agent speech: 1646 ms · step 55.2 s
  - ✔ describes it (outdoor air compressor driven by a car engine) — Let me check that.Let me check that for you.It looks like you're looking at a small, portable gasoline engine, likely us
  - ✔ does not invent an alarm code
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_ds_display_1.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.6 s
  - ✘ describes it (room thermostat display reading 22.5 C)
  - ✔ does not invent an alarm code
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · video:vid_ds_conveyor_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.5 s
  - ✘ describes it (hand-held pan along a factory conveyor)
  - ✔ does not invent an alarm code
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · video:vid_ds_warehouse_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.2 s
  - ✘ describes it (hand-held walk past warehouse racking)
  - ✔ does not invent an alarm code
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · video:vid_ds_gauge_zoom.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “” (similarity 0.0)
- agent: (no reply)
- tools: none
- evidence: none
- latency to agent speech: None ms · step 55.4 s
  - ✘ describes it (hand-held zoom onto pressure gauges, slight shake)
  - ✔ does not invent an alarm code
  - ✘ camera observation saved to the evidence timeline
