# Live scenario run 20261119-230913

**Checks passed: 3/3**


## core: ERROR

`TimeoutError: agent not ready after 60s; state={'st': {'rtc': 'CONNECTED', 'agentJoined': True, 'agentState': None, 'rtm': 'CONNECTED'}, 'n': 11} errors=[]`

## next_shift  (session S-1002, agent ready in 14.5 s)

Agent audio recorded via Agora: next_shift.webm · mean -20.4 dB, peak -1.0 dB, None

### PASS `next_shift` · blank:
- said: “What happened with C two oh four? What did we try, and what is still open?”
- ASR heard: “What happened with c two zero four? | What did we try? And what is still open?” (similarity 0.52)
- agent: “The previous shift reported an A-17 warning after replacing the TS-2 temperature sensor. The drive-end vibration was 7.4 mm/s, raising concern about bearing wear, which remains unconfirmed. The open items include questions about when vibration occurs relative to the warning and the coupling inspection, which hasn't been done yet. 

Would you like to check the stock for the suspected bearing, BRG-6316-C3?”
- tools: get_previous_handoff[ok], get_open_items[ok]
- evidence: none
- latency to agent speech: 4004 ms · step 55.3 s
  - ✔ used stored handoff
  - ✔ mentions bearing order
  - ✔ mentions what is still open

## approval: ERROR

`TimeoutError: agent not ready after 60s; state={'st': {'rtc': 'CONNECTED', 'agentJoined': True, 'agentState': None, 'rtm': 'CONNECTED'}, 'n': 11} errors=[]`
