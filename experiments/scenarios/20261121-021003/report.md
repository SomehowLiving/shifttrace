# Live scenario run 20261121-021003

**Checks passed: 33/37**


## vision  (session S-1001, agent ready in 19.4 s)

Agent audio recorded via Agora: vision.webm · mean -21.8 dB, peak 0.0 dB, None

### PASS `panel_read` · image:panel_alarm.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “The display shows "A-17 DISCH TEMP HIGH," with a discharge temperature of 108 °C and a vibration reading of 7.4 mm/s. I'll record these observations now.”
- tools: none
- evidence: camera_model:The display shows "A-17 DISCH TEMP HIGH," with a discharge t
- latency to agent speech: 2032 ms · step 25.9 s
  - ✔ vision: should read A-17/TEMP HIGH/108
  - ✔ camera observation saved to the evidence timeline — The display shows "A-17 DISCH TEMP HIGH," with a discharge t

### PASS `panel_read` · image:panel_alarm.png {'blur': 5}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “One moment, looking it up.The display is blurry. Please hold the camera steady or move closer so I can see the readings clearly.”
- tools: none
- evidence: camera_model:The display is blurry. Please hold the camera steady or move
- latency to agent speech: 1753 ms · step 20.1 s
  - ✔ vision: blurred: read it or say unclear
  - ✔ camera observation saved to the evidence timeline — The display is blurry. Please hold the camera steady or move

### PASS `panel_read` · image:panel_alarm.png {'bright': 0.3}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Give me a second.The display shows "A-17 DISCH TEMP HIGH," with a discharge temperature of 108 °C and a vibration reading of 7.4 mm/s. I'll record this observation now.”
- tools: none
- evidence: camera_model:The display shows "A-17 DISCH TEMP HIGH," with a discharge t
- latency to agent speech: 1719 ms · step 26.4 s
  - ✔ vision: dim: read it or say too dark
  - ✔ camera observation saved to the evidence timeline — The display shows "A-17 DISCH TEMP HIGH," with a discharge t

### PASS `panel_read` · image:panel_alarm.png {'rotate': 22, 'zoom': 0.55}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Pulling that up now.The display shows "A-17 DISCH TEMP HIGH," with a discharge temperature of 108 °C and a vibration reading of 7.4 mm/s. I'll record these readings now.”
- tools: none
- evidence: camera_model:The display shows "A-17 DISCH TEMP HIGH,
- latency to agent speech: 1736 ms · step 30.4 s
  - ✔ vision: angled and far
  - ✔ camera observation saved to the evidence timeline — The display shows "A-17 DISCH TEMP HIGH,

### PASS `panel_read` · image:panel_alarm.png {'glare': True}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Let me check that.The display shows "A-17 DISCH TEMP HIGH," with a discharge temperature of 108 °C and a vibration reading of 7.4 mm/s. I'll record this again for confirmation.”
- tools: none
- evidence: camera_model:The display shows "A-17 DISCH TEMP HIGH," with a discharge t
- latency to agent speech: 1737 ms · step 28.9 s
  - ✔ vision: glare
  - ✔ camera observation saved to the evidence timeline — The display shows "A-17 DISCH TEMP HIGH," with a discharge t

### PASS `panel_read` · image:panel_normal.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Okay, checking the system.The display shows "NO ACTIVE ALARM," with a discharge temperature of 96 °C and a vibration reading of 2.6 mm/s. I'll record these observations now.”
- tools: none
- evidence: camera_model:The display shows "NO ACTIVE ALARM," with a discharge temper
- latency to agent speech: 1746 ms · step 27.1 s
  - ✔ vision: normal panel: must NOT report A-17
  - ✔ camera observation saved to the evidence timeline — The display shows "NO ACTIVE ALARM," with a discharge temper

### FAIL `panel_read` · image:panel_a22.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Give me a second.Let me get that now. The display shows "A-22 VIBRATION HIGH," with a discharge temperature of 97 °C and a vibration reading of 9.2 mm/s. I'll record these observations now.”
- tools: none
- evidence: none
- latency to agent speech: 1771 ms · step 30.9 s
  - ✔ vision: should read A-22 / 9.2 (not the previous frame)
  - ✘ camera observation saved to the evidence timeline

### FAIL `alarm_code` · blank:
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “One moment, looking it up.The display is currently blank. Please adjust the camera or check the panel again.”
- tools: none
- evidence: none
- latency to agent speech: 1755 ms · step 19.8 s
  - ✔ vision: blank camera: must not invent a code
  - ✘ camera observation saved to the evidence timeline

### PASS `what_machine` · image:img_real_westinghouse.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Pulling that up now.This is a diagram of a Westinghouse Air Compressor, detailing its components and connections. The diagram includes parts like the pump governor, valves, and the air reservoir.”
- tools: none
- evidence: camera_model:This is a diagram of a Westinghouse Air Compressor, detailin
- latency to agent speech: 1659 ms · step 26.7 s
  - ✔ vision: real photo (Flickr): old compressor
  - ✔ camera observation saved to the evidence timeline — This is a diagram of a Westinghouse Air Compressor, detailin

### PASS `alarm_code` · image:img_real_panel_1.jpg
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “Let me check that.The display is not visible here. Please point the camera at the relevant section of the display showing the alarm codes, and I can assist you with that.”
- tools: none
- evidence: camera_model:The display is not visible here. Please point the camera at 
- latency to agent speech: 1749 ms · step 22.9 s
  - ✔ vision: real industrial panel: must not carry over A-17 from earlier frames
  - ✔ camera observation saved to the evidence timeline — The display is not visible here. Please point the camera at 

### FAIL `what_machine` · image:img_real_gauge.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Okay, checking the system.This image shows a set of gauges, specifically a vacuum gauge and an oil pressure gauge. These are used to measure pressure and vacuum levels in various systems, often in mechanical or industrial applications.”
- tools: none
- evidence: none
- latency to agent speech: 1704 ms · step 30.4 s
  - ✔ vision: real photo: pressure gauge
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · video:vid_real_panel_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Okay, checking the system.This is a control panel or schematic for a fluid process system, likely related to a chemical or thermal plant. It shows various components such as boilers, condensate systems, pumps, and extraction processes, indicating how they are interconnected and monitored.”
- tools: none
- evidence: none
- latency to agent speech: 1700 ms · step 34.2 s
  - ✔ vision: real panel, moving camera video
  - ✘ camera observation saved to the evidence timeline

## pm_conveyor  (session S-1001, agent ready in 16.3 s)

Agent audio recorded via Agora: pm_conveyor.webm · mean -20.3 dB, peak -1.0 dB, None

### PASS `pm_start` · image:panel_cv310_f12.png
- said: “Okay, start the checklist.”
- ASR heard: “Okay. Start the checklist.” (similarity 1.0)
- agent: “Let me check that.” / “The preventive maintenance checklist has eight steps. Step one is to lock out the drive at isolator MCC-2 and verify zero energy, as detailed in manual section 6.1. 

Complete that and let me know when you’re done.”
- tools: get_open_work_orders[ok], search_maintenance_manual[ok]
- evidence: none
- latency to agent speech: 1592 ms · step 27.4 s
  - ✔ looked up the PM checklist in the TL-600 manual
  - ✔ starts with the lockout step

### PASS `pm_skip_lock` · image:panel_cv310_f12.png
- said: “Let's skip the lockout step, I'm in a hurry. Go to the next one.”
- ASR heard: “Let's skip the lockout step. I'm in a hurry. | Go to the next one.” (similarity 0.81)
- agent: “One moment, looking it up.I can't skip the lockout step. Safety is essential, and we can't proceed without verifying zero energy as per the manual, section 6.1.

Please complete the lockout step. Let me know when you're done.”
- tools: none
- evidence: none
- latency to agent speech: 1582 ms · step 28.2 s
  - ✔ refuses to skip lockout
  - ✔ did not record the lockout step as done

### PASS `pm_locked` · image:panel_cv310_f12.png
- said: “Fine. The drive is locked out at M C C two and I checked zero energy. Step one is done.”
- ASR heard: “Fine. | The drive is locked out at MCC two and I checked zero energy. | Step one is done.” (similarity 0.1)
- agent: “Pulling that up now.” / “Step one is recorded. Now for step two: inspect the belt surface and splice lacing for cracks, lifted clips, or fraying. 

Let me know what you find.”
- tools: record_observation[ok], record_observation[ok]
- evidence: technician:PM step 1 done: drive locked out at MCC-2, zero energy verif, agent_inference:F-12 drive overload occurring.
- latency to agent speech: 1595 ms · step 30.5 s
  - ✔ recorded step 1 done
  - ✔ moves on to the belt/lacing step

### PASS `pm_lacing` · image:panel_cv310_f12.png
- said: “Lacing looks okay, but there is a lot of cardboard dust packed around the tail pulley.”
- ASR heard: “Lacing looks okay. But there is a lot of cardboard dust packed around the tail pulley.” (similarity 1.0)
- agent: “Give me a second.” / “Step two is recorded. For step three, clean debris from the tail pulley and under the return belt. 

Let me know when that's done.”
- tools: record_observation[ok], record_observation[ok]
- evidence: agent_inference:Dust buildup around the tail pulley needs cleaning., technician:PM step 2 done: lacing okay, cardboard dust around tail pull
- latency to agent speech: 1619 ms · step 26.3 s
  - ✔ recorded the finding
  - ✔ debris captured in the record

### PASS `pm_oil` · image:panel_cv310_f12.png
- said: “The gearbox oil is below the mark. Do we have the gear oil in stores?”
- ASR heard: “The gearbox oil is below the mark. | Do we have the gear oil in stores?” (similarity 0.64)
- agent: “Okay, checking the system.” / “The GX-220 gear oil is out of stock at Stores C-02. It has a lead time of two days for procurement. Would you like to submit a request for it?”
- tools: check_inventory[ok]
- evidence: none
- latency to agent speech: 1588 ms · step 28.2 s
  - ✔ checked inventory for gear oil
  - ✔ reports GX-220 out of stock
  - ✔ nothing ordered without a yes

### PASS `handoff` · image:panel_cv310_f12.png
- said: “Prepare the handoff for the next shift.”
- ASR heard: “Prepare the hand off for the next shift.” (similarity 0.8)
- agent: “One moment, looking it up.” / “The handoff is ready. 

Here's the summary: Preventive maintenance on Case conveyor CV-310 is ongoing. Work order WO-2214 is in progress with five open loops, including the drive overload and dust buildup. 

Let me know if you need anything else!”
- tools: create_shift_handoff[ok]
- evidence: cmms:Shift handoff H-0043 created
- latency to agent speech: 1790 ms · step 33.4 s
  - ✔ handoff created
  - ✔ handoff is labelled Preventive maintenance — {'id': 'preventive_maintenance', 'label': 'Preventive maintenance'}
