"""Visual evidence is captured from the agent's spoken camera description when it did not record it itself."""
import asyncio

from app import capture, services as svc
from app.db import connect, tx, utcnow


def _session():
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status) VALUES ('S-1001','C-204','Kavya Rao','A shift',?, 'ACTIVE')", (utcnow(),))
    return "S-1001"


def _say(sid, role, turn, text):
    with tx() as conn:
        svc.add_transcript(conn, sid, role, turn, text, True)


def _visuals(sid):
    conn = connect()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM evidence WHERE session_id=? AND event_type='visual_observation'", (sid,))]
    finally:
        conn.close()


def test_captures_spoken_camera_description():
    capture._scheduled.clear()
    sid = _session()
    _say(sid, "user", "2", "What does the panel display show right now?")
    _say(sid, "agent", "3", "The panel shows A-22 VIBRATION HIGH at 97 °C and 9.2 mm/s. I'll record this observation.")
    asyncio.run(capture.on_agent_utterance(sid, "3"))
    v = _visuals(sid)
    assert len(v) == 1 and v[0]["source_type"] == "camera_model" and v[0]["status"] == "unverified"
    assert "A-22" in v[0]["title"] and "captured_by" in v[0]["payload_json"]
    asyncio.run(capture.on_agent_utterance(sid, "3"))  # same turn again: no duplicate
    assert len(_visuals(sid)) == 1


def test_no_capture_when_agent_recorded_it_or_question_not_visual():
    capture._scheduled.clear()
    sid = _session()
    _say(sid, "user", "2", "What do you see?")
    with tx() as conn:
        svc.record_evidence(conn, session_id=sid, asset_id="C-204", event_type="visual_observation", source_type="camera_model",
                            title="TEMP HIGH lamp lit")
    _say(sid, "agent", "3", "I see the TEMP HIGH lamp is lit.")
    asyncio.run(capture.on_agent_utterance(sid, "3"))
    assert len(_visuals(sid)) == 1  # only the agent's own record
    _say(sid, "user", "4", "Do we have the drive end bearing in stores?")
    _say(sid, "agent", "5", "It shows zero available in stores.")
    asyncio.run(capture.on_agent_utterance(sid, "5"))
    assert len(_visuals(sid)) == 1


def test_filler_prefix_stripped_and_cannot_see_captured():
    capture._scheduled.clear()
    sid = _session()
    _say(sid, "user", "2", "Read me the alarm code on the display.")
    _say(sid, "agent", "3", "One moment, looking it up.It seems I'm unable to see any specific alarm codes in the current view.")
    asyncio.run(capture.on_agent_utterance(sid, "3"))
    v = _visuals(sid)
    assert len(v) == 1 and v[0]["title"].startswith("It seems I'm unable to see")


def test_back_to_back_camera_questions_each_get_captured():
    """21 Nov run: a fixed 20 s window let the previous answer's capture suppress the next camera question."""
    from app import capture
    from app.db import tx, utcnow
    from app import services as svc2
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status) VALUES ('S-1009','C-204','Kavya Rao','A shift',?, 'ACTIVE')", (utcnow(),))
        svc2.record_evidence(conn, session_id="S-1009", asset_id="C-204", event_type="visual_observation", source_type="camera_model",
                             title="previous answer", status="unverified")
    import time
    time.sleep(1.1)
    with tx() as conn:
        svc2.add_transcript(conn, "S-1009", "user", "5", "What kind of equipment am I looking at?", True)
        svc2.add_transcript(conn, "S-1009", "agent", "5", "Let me check that.You're looking at a set of mechanical gauges.", True)
    ok, text = capture.should_capture("S-1009", "5")
    assert ok and text.startswith("You're looking at")


def test_visual_answer_phrasings_seen_live_are_recognised():
    from app.capture import VISUAL_A, strip_fillers
    for said in ["One moment, looking it up.This is a set of gauges, including a vacuum gauge.",
                 "Pulling that up now.It seems the display is not clear. Please point the camera at the panel.",
                 "It seems the camera is not capturing the display clearly."]:
        assert VISUAL_A.search(strip_fillers(said)), said


def test_filler_only_turn_is_re_armed_until_the_answer_arrives():
    import asyncio
    from app import capture
    from app import services as svc2
    from app.db import connect, tx, utcnow
    with tx() as conn:
        conn.execute("INSERT INTO sessions(session_id, asset_id, technician, shift_label, started_at, status) VALUES ('S-1010','C-204','Kavya Rao','A shift',?, 'ACTIVE')", (utcnow(),))
        svc2.add_transcript(conn, "S-1010", "user", "7", "What does the panel display show right now?", True)
        svc2.add_transcript(conn, "S-1010", "agent", "7", "Give me a second.", True)
    asyncio.run(capture.on_agent_utterance("S-1010", "7"))          # filler only: nothing recorded, re-armed
    with tx() as conn:
        svc2.add_transcript(conn, "S-1010", "agent", "7", "Give me a second.The display shows A-22 VIBRATION HIGH and 9.2 mm/s.", True)
    asyncio.run(capture.on_agent_utterance("S-1010", "7"))
    conn = connect()
    try:
        rows = conn.execute("SELECT title FROM evidence WHERE session_id='S-1010' AND source_type='camera_model'").fetchall()
    finally:
        conn.close()
    assert [r[0] for r in rows] == ["The display shows A-22 VIBRATION HIGH and 9.2 mm/s."]


def test_capture_recognises_common_description_phrasings():
    from app.capture import VISUAL_A
    for text in ["It looks like you are viewing a storage facility with shelves of boxes.",
                 "It seems you are looking at a warehouse section.", "You're viewing HVAC ductwork."]:
        assert VISUAL_A.search(text), text
