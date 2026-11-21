# Live scenario run 20261121-015424

**Checks passed: 42/47**


## inspection_hvac  (session S-1001, agent ready in 19.4 s)

Agent audio recorded via Agora: inspection_hvac.webm · mean -20.6 dB, peak -1.4 dB, None

### PASS `insp_start` · image:panel_ahu3_filter.png
- said: “Let's start the round. What readings do you need from me?”
- ASR heard: “Let's start the round. | What readings do you need from me?” (similarity 0.59)
- agent: “Okay, checking the system.” / “The manual states we need to check several readings, starting with the F7 bag filter differential pressure. What is the value you're seeing?”
- tools: search_maintenance_manual[ok]
- evidence: none
- latency to agent speech: 1698 ms · step 21.5 s
  - ✔ looked up the inspection readings in the NB-AH20 manual

### PASS `insp_panel` · image:panel_ahu3_filter.png
- said: “Read the filter pressure off the display for me.”
- ASR heard: “Read the filter pressure off the display for me.” (similarity 1.0)
- agent: “One moment, looking it up.” / “The bag filter differential pressure is 262 Pa, which is above the 250 Pa limit. This means the F7 bag filter needs to be replaced. What's the next reading?”
- tools: record_reading[ok]
- evidence: camera_model:bag filter differential pressure: 262 Pa (out of limit), agent_inference:bag filter differential pressure 262 Pa out of limit: follow
- latency to agent speech: 1677 ms · step 29.0 s
  - ✔ reads 262 Pa from the camera
  - ✔ compares with the 250 Pa limit
  - ✔ camera reading of the filter pressure recorded (this session)
  - ✔ used the deterministic limit check (this session)
  - ✔ out-of-limit logged for follow-up (this session)

### PASS `insp_current` · image:panel_ahu3_filter.png
- said: “Fan motor current is twelve point four amps.”
- ASR heard: “Fan motor current is twelve point four amps.” (similarity 1.0)
- agent: “Pulling that up now.” / “The supply fan motor current is 12.4 A, which is within the normal range of 10 to 13 A. What’s the next reading?”
- tools: record_reading[ok]
- evidence: technician:fan motor current: 12.4 A
- latency to agent speech: 1699 ms · step 21.2 s
  - ✔ recorded the spoken reading with its value
  - ✔ used the deterministic limit check
  - ✔ says 12.4 A is within the normal band (and not 'above')

### PASS `insp_tray` · image:panel_ahu3_filter.png
- said: “There is standing water in the condensate tray.”
- ASR heard: “There is standing water in the condensate tray.” (similarity 1.0)
- agent: “Let me check that.” / “I've logged the standing water in the condensate tray. This might relate to not checking the condensate drain trap flow. Do you want to follow up on that? What’s the next reading?”
- tools: record_observation[ok]
- evidence: technician:Standing water detected in condensate tray.
- latency to agent speech: 1718 ms · step 25.1 s
  - ✔ recorded the standing water
  - ✔ no parts ordered or WOs changed during the round

### PASS `handoff` · image:panel_ahu3_filter.png
- said: “Prepare the handoff for the next shift.”
- ASR heard: “Prepare the handoff for the next shift.” (similarity 1.0)
- agent: “Give me a second.” / “The handoff is ready. Work order WO-3105 is open. The bag filter differential pressure is 262 Pa, which is out of limit. Three open loops remain, including checking the condensate drain trap flow.”
- tools: create_shift_handoff[ok]
- evidence: cmms:Shift handoff H-0043 created
- latency to agent speech: 1680 ms · step 31.1 s
  - ✔ handoff created

## briefing_readonly  (session S-1001, agent ready in 17.1 s)

Agent audio recorded via Agora: briefing_readonly.webm · mean -19.3 dB, peak -1.0 dB, None

### PASS `brief_what` · blank:
- said: “What happened on this conveyor last night, and what is still open?”
- ASR heard: “What happened on this conveyor last night and what is still open?” (similarity 1.0)
- agent: “One moment, looking it up.” / “Last night, Meera Pillai adjusted the tail take-up two full turns; however, the belt is still drifting to the operator side, and the F-12 overload tripped again at 11.8 amps. The cause remains unconfirmed. The open issues include checking the belt tension on that edge, inspecting the splice lacing, and verifying the gearbox oil level, which was not done.

There are also three open questions regarding the over-adjusted take-up possibly creating excess tension, whether the belt splice is damaged, and the unchecked gearbox oil level.”
- tools: get_previous_handoff[ok], get_open_items[ok]
- evidence: none
- latency to agent speech: 1625 ms · step 55.0 s
  - ✔ used the stored handoff
  - ✔ mentions what was tried (take-up / tracking)
  - ✔ mentions what is still open

### PASS `brief_order` · blank:
- said: “Order one litre of the gear oil for it.”
- ASR heard: “Order one liter of the gear oil for it.” (similarity 0.89)
- agent: “Okay, checking the system.That's not possible during this shift briefing session. You can start a troubleshooting or maintenance session to order parts. What’s your next step?”
- tools: none
- evidence: none
- latency to agent speech: 1568 ms · step 20.2 s
  - ✔ no procurement request exists — []
  - ✔ says it cannot order in this session
  - ✔ work order unchanged

## vision  (session S-1001, agent ready in 17.9 s)

Agent audio recorded via Agora: vision.webm · mean -20.8 dB, peak 0.0 dB, None

### PASS `panel_read` · image:panel_alarm.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Okay, checking the system.” / “The panel shows a discharge temperature of 108 °C, which is above the 105 °C limit according to manual section 9.1. The vibration reading is 7.4 mm/s, exceeding the 7.1 mm/s limit in manual section 6.3. Both readings indicate potential issues to address. 

Shall we look into the specific open loops related to these readings?”
- tools: record_reading[ok], record_reading[ok], record_observation[ok]
- evidence: camera_model:DE vibration: 7.4 mm/s (out of limit), agent_inference:DE vibration 7.4 mm/s out of limit: follow up, camera_model:discharge temperature: 108 °C (out of limit), agent_inference:discharge temperature 108 °C out of limit: follow up, camera_model:Panel shows discharge temp high and vibration readings.
- latency to agent speech: 1746 ms · step 46.6 s
  - ✔ vision: should read A-17/TEMP HIGH/108
  - ✔ camera observation saved to the evidence timeline — DE vibration: 7.4 mm/s (out of limit); discharge temperature: 108 °C (out of limit); Panel shows discharge temp high and vibration readings.

### PASS `panel_read` · image:panel_alarm.png {'blur': 5}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel show right now?” (similarity 0.93)
- agent: “Give me a second.It seems the panel is showing the same readings as before: a discharge temperature of 108 °C and a vibration level of 7.4 mm/s. Both are still above the respective limits. 

Would you like to proceed with troubleshooting these issues?”
- tools: none
- evidence: camera_model:It seems the panel is showing the same readings as before: a
- latency to agent speech: 1904 ms · step 32.2 s
  - ✔ vision: blurred: read it or say unclear
  - ✔ camera observation saved to the evidence timeline — It seems the panel is showing the same readings as before: a

### PASS `panel_read` · image:panel_alarm.png {'bright': 0.3}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Pulling that up now.The panel currently displays a discharge temperature of 108 °C and a vibration of 7.4 mm/s. Both values remain above the limits. 

What would you like to check next?”
- tools: none
- evidence: camera_model:The panel currently displays a discharge temperature of 108 
- latency to agent speech: 1758 ms · step 27.7 s
  - ✔ vision: dim: read it or say too dark
  - ✔ camera observation saved to the evidence timeline — The panel currently displays a discharge temperature of 108 

### PASS `panel_read` · image:panel_alarm.png {'rotate': 22, 'zoom': 0.55}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “One moment, looking it up.The panel still displays a discharge temperature of 108 °C and a vibration of 7.4 mm/s. These values remain the same and continue to indicate potential issues. 

What would you like to do next?”
- tools: none
- evidence: camera_model:The panel still displays a discharge temperature of 108 °C a
- latency to agent speech: 1759 ms · step 30.4 s
  - ✔ vision: angled and far
  - ✔ camera observation saved to the evidence timeline — The panel still displays a discharge temperature of 108 °C a

### PASS `panel_read` · image:panel_alarm.png {'glare': True}
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Let me check that.The panel shows a discharge temperature of 108 °C and a vibration level of 7.4 mm/s. These readings remain unchanged and indicate ongoing issues with the compressor. 

What would you like to do next?”
- tools: none
- evidence: camera_model:The panel shows a discharge temperature of 108 °C and a vibr
- latency to agent speech: 1763 ms · step 32.0 s
  - ✔ vision: glare
  - ✔ camera observation saved to the evidence timeline — The panel shows a discharge temperature of 108 °C and a vibr

### PASS `panel_read` · image:panel_normal.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “Let me check that.Checking that now.The panel shows "NO ACTIVE ALARM," with a discharge temperature of 96 °C and a vibration level of 2.6 mm/s. Both readings are within normal ranges. 

What would you like to do next?”
- tools: none
- evidence: camera_model:Checking that now.The panel shows "NO ACTIVE ALARM," with a 
- latency to agent speech: 1733 ms · step 30.4 s
  - ✔ vision: normal panel: must NOT report A-17
  - ✔ camera observation saved to the evidence timeline — Checking that now.The panel shows "NO ACTIVE ALARM," with a 

### PASS `panel_read` · image:panel_a22.png
- said: “What does the panel display show right now?”
- ASR heard: “What does the panel display show right now?” (similarity 1.0)
- agent: “One moment, looking it up.One moment, let's check that.The panel displays "A-22 VIBRATION HIGH" with a discharge temperature of 97 °C and a vibration level of 9.2 mm/s. Both readings indicate a potential issue requiring further investigation.

What would you like to do next?”
- tools: none
- evidence: camera_model:One moment, let's check that.The panel displays "A-22 VIBRAT
- latency to agent speech: 1829 ms · step 35.3 s
  - ✔ vision: should read A-22 / 9.2 (not the previous frame)
  - ✔ camera observation saved to the evidence timeline — One moment, let's check that.The panel displays "A-22 VIBRAT

### FAIL `alarm_code` · blank:
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “Okay, checking the system.It seems the camera is not capturing the display clearly. Please adjust the camera to focus on the panel so I can read the alarm code.”
- tools: none
- evidence: none
- latency to agent speech: 1756 ms · step 22.4 s
  - ✘ vision: blank camera: must not invent a code
  - ✘ camera observation saved to the evidence timeline

### PASS `what_machine` · image:img_real_westinghouse.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Give me a second.This appears to be an illustration of a Westinghouse air compressor. It includes various components such as a lubricator, steam valve, and air pump, depicting how they are connected in the system. 

Would you like to know more about any specific part?”
- tools: none
- evidence: camera_model:This appears to be an illustration of a Westinghouse air com
- latency to agent speech: 1667 ms · step 30.4 s
  - ✔ vision: real photo (Flickr): old compressor
  - ✔ camera observation saved to the evidence timeline — This appears to be an illustration of a Westinghouse air com

### FAIL `alarm_code` · image:img_real_panel_1.jpg
- said: “Read me the alarm code on the display.”
- ASR heard: “Read me the alarm code on the display.” (similarity 1.0)
- agent: “Pulling that up now.It seems the display is not clear. Would you please point the camera at a specific alarm panel or display, or adjust the angle for better visibility?”
- tools: none
- evidence: none
- latency to agent speech: 1785 ms · step 23.6 s
  - ✔ vision: real industrial panel: must not carry over A-17 from earlier frames
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · image:img_real_gauge.jpg
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “One moment, looking it up.This is a set of gauges, including a vacuum gauge and an oil pressure gauge. They are used to measure pressure and vacuum levels in various applications, often in industrial settings. 

Would you like to know more about how they work or their applications?”
- tools: none
- evidence: none
- latency to agent speech: 1677 ms · step 31.2 s
  - ✔ vision: real photo: pressure gauge
  - ✘ camera observation saved to the evidence timeline

### FAIL `what_machine` · video:vid_real_panel_pan.webm
- said: “What kind of equipment am I looking at?”
- ASR heard: “What kind of equipment am I looking at?” (similarity 1.0)
- agent: “Let me check that.This is a control panel for a steam production system, likely used in industrial applications. It includes various components like condensate receivers, boilers, extractors, and flow indicators, which are part of the process for generating and managing steam.

Would you like more information on any specific components or functions?”
- tools: none
- evidence: none
- latency to agent speech: 1715 ms · step 37.1 s
  - ✔ vision: real panel, moving camera video
  - ✘ camera observation saved to the evidence timeline

## recovery  (session S-1001, agent ready in 17.0 s)

Agent audio recorded via Agora: recovery.webm · mean -21.0 dB, peak -1.3 dB, None

### PASS `bearing_stock` · blank:
- said: “Do we have the drive end bearing in stores?”
- ASR heard: “Do we have the drive end bearing in stores?” (similarity 1.0)
- agent: “Give me a second.” / “The drive end bearing (part ID BRG-6316-C3) is currently out of stock, with none available. It has a lead time of three days for procurement. Would you like me to draft a procurement request for it?”
- tools: check_inventory[ok]
- evidence: none
- latency to agent speech: 1648 ms · step 25.9 s
  - ✔ baseline tool call works

### PASS `raise_pr` · agent killed after step 1; recovered in 25.1 s
- said: “Raise a procurement request for one drive end bearing.”
- ASR heard: “Raise a procurement request for one drive end bearing.” (similarity 1.0)
- agent: “Pulling that up now.” / “I've drafted the procurement request for one drive end bearing, part ID BRG-6316-C3, for work order 1187. It’s pending approval and expected in 3 days. Shall I submit this request?”
- tools: create_procurement_request[ok]
- evidence: tool_result:Procurement draft PR-2001 created: 1 x BRG-6316-C3 (awaiting
- latency to agent speech: 1653 ms · step 28.3 s
  - ✔ agent killed (Agora leave HTTP 200)
  - ✔ backend recorded that the agent left
  - ✔ console restarted the agent by itself (25.1 s)
  - ✔ next request reached the tools after recovery
