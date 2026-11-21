"""Test feed (demo_data/testkit.json): offered per machine and task, and only listed files are served."""
from fastapi.testclient import TestClient

from app import testkit
from app.api import create_app


def test_offers_scenes_and_lines_for_the_machine_and_task():
    kit = testkit.for_session("C-204", "troubleshoot")
    scenes = {s["id"] for s in kit["scenes"]}
    assert "c204_alarm" in scenes and "cv310_f12" not in scenes
    lines = {l["id"]: l for l in kit["lines"]}
    assert "prev_shift" in lines and "pm_start" not in lines and "insp_current" not in lines
    assert lines["look_panel"]["scene"] == "c204_alarm"
    assert lines["prev_shift"]["text"].startswith("What happened to this compressor")
    pm = {l["id"] for l in testkit.for_session("CV-310", "preventive_maintenance")["lines"]}
    assert {"pm_start", "pm_skip_lock", "look_panel_cv310"} <= pm and "prev_shift" not in pm


def test_every_listed_file_exists():
    kit = testkit._kit()
    for item in kit["scenes"] + kit["lines"]:
        assert testkit.media_path(item["file"]) is not None, item["file"]


def test_media_endpoint_serves_only_listed_files():
    c = TestClient(create_app())
    r = c.get("/api/testkit/media/panel_alarm.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert c.get("/api/testkit/media/utterances.json").status_code == 404
    r = c.get("/api/testkit/media/..%2F..%2Fbackend%2F.env")  # falls through to the console's index.html, never the file
    assert r.status_code == 404 or (r.headers["content-type"].startswith("text/html") and "MURF_API_KEY" not in r.text and "AGORA" not in r.text)
    assert c.get("/api/testkit?asset_id=AHU-3&task_id=inspection_round").json()["lines"][0]["id"] == "look_panel_ahu3"
