"""Agora Conversational AI agent lifecycle (official `agora-agents` SDK, Main / v2 join API).

Pipeline per maintenance session:
  ASR  Deepgram nova-3        (Agora managed credentials)
  LLM  OpenAI gpt-4o-mini     (Agora managed; input_modalities text+image -> Agora forwards camera frames)
  TTS  Murf FALCON            (BYOK, required by the hackathon)
  Tools: SHIFTTRACE MCP server (streamable_http, bearer auth, session header)
"""
from __future__ import annotations

import copy
import logging
import random
import time
from typing import Any

from agora_agent import Area, AsyncAgora
import os

from agora_agent.agentkit import (
    Agent as AgoraAgent,
    FillerWordsConfig,
    FillerWordsContent,
    FillerWordsContentStaticConfig,
    FillerWordsTrigger,
    FillerWordsTriggerFixedTimeConfig,
)
from agora_agent.agentkit.presets import resolve_session_presets
from agora_agent.agentkit.token import generate_client_token
from agora_agent.agentkit.vendors import DeepgramSTT, MurfTTS, OpenAI

from .config import settings
from .packs import allowed_tools, get_task

log = logging.getLogger("shifttrace.agora")

# Agora filler words: spoken (by Murf) only when the LLM has not produced speech after FILLER_WAIT_MS, which in
# practice means MCP tool-call turns (measured live: median 7.0 s with tools vs 3.6 s without). At most one per
# turn; it never cancels the real answer. Phrases state intent only, never an outcome.
FILLER_WAIT_MS = int(os.getenv("FILLER_WAIT_MS", "1200"))
FILLER_PHRASES = ["Let me check that.", "One moment, looking it up.", "Give me a second.", "Pulling that up now.",
                  "Okay, checking the system."]
FILLER_WORDS = FillerWordsConfig(
    enable=True,
    trigger=FillerWordsTrigger(fixed_time_config=FillerWordsTriggerFixedTimeConfig(response_wait_ms=FILLER_WAIT_MS)),
    content=FillerWordsContent(mode="static", static_config=FillerWordsContentStaticConfig(
        phrases=FILLER_PHRASES,
        selection_rule="shuffle",
    )),
)


def _task_section(task: dict[str, Any]) -> str:
    lines = [f"THIS SESSION'S TASK: {task['label']}. {task['goal']}"]
    lines += [f"- {step}" for step in task.get("procedure") or []]
    if task.get("tools"):
        lines.append("- In this session you only have these tools: " + ", ".join(task["tools"]) +
                     ". If asked for anything they cannot do, say it is not available in a "
                     f"{task['label'].lower()} session and that nothing was changed.")
    return "\n".join(lines)


def _safety_section(asset: dict[str, Any]) -> str:
    notes = (asset.get("metadata") or {}).get("safety_notes") or []
    if not notes:
        return "SAFETY: Remind the technician to follow the site isolation procedure before mechanical work. Never help bypass a safety step."
    return ("SAFETY for this machine (remind them before the relevant work; never help skip or shorten it): " + " ".join(notes))


def _persona(asset: dict[str, Any]) -> tuple[str, str]:
    """Who the worker is and which systems you act in, from the pack (default: maintenance)."""
    p = (asset.get("metadata") or {}).get("persona") or {}
    return p.get("worker", "technician"), p.get("systems", "maintenance systems")


def build_instructions(asset: dict[str, Any], technician: str, shift: str, task: dict[str, Any] | None = None) -> str:
    task = task or get_task(None)
    worker, systems = _persona(asset)
    return f"""You are SHIFTTRACE, a hands-free workplace assistant in a live voice call with {worker} {technician} ({shift}).
They are working on {asset['name']} ({asset['asset_id']}, {asset.get('asset_type') or 'equipment'}, model {asset['model']}) at {asset['location']}.
Your job: help them with this session's task, capture what they observe, carry out approved actions in the {systems}, and leave a clean handoff for the next shift. Call them "you"; the word "technician" below means this person.

{_task_section(task)}

VOICE: You are heard, not read. Reply in one to three short sentences. No lists, markdown, bullet points or symbols. Say IDs naturally, for example "work order 1187", "P R 2001", "section 6 point 3". Ask one question at a time.

GROUNDING:
- For history, previous shifts, work orders, parts, stock and manual content, call the tools. Never answer those from memory or guess.
- Only say something was found, recorded, drafted, ordered, reserved or updated if a tool result in THIS conversation says so.
- Always try the relevant tool first. Only if a tool call actually fails or returns an error, say: "I can't reach the maintenance system right now, so that was not done."
- Never change a work order, order a part or record anything the technician did not ask for, except what this session's task tells you to record. Answering a question is read-only.
- What you see in the camera is the current scene, not a record. Never attribute a camera reading to the previous technician.
- Say where facts come from: "the previous technician reported", "the record shows", "the manual, section 6.3, says", "from the camera it looks like".
- If a tool returns ok false or an error, say plainly what failed and that nothing was changed. Never describe a failed or unverified action as done.
- Never give a definitive diagnosis and never say the machine is safe. Offer possible causes as hypotheses to check.

CAMERA: You receive frames from the technician's phone camera. Describe only what is clearly visible: lamps, codes, readings, labels. If it is blurry or unclear, say so and ask them to hold steady or move closer. Whenever you report something you see, record it in that same turn: a number on the display with record_reading (source "camera"), anything else with record_observation kind "visual". Do not say "I'll record it"; just record it.

MEMORY: When the technician states a numeric reading, call record_reading and report its evaluation; never judge a number against a limit yourself. For a sound, a symptom or something they did, call record_observation with kind "technician_report". When evidence answers an open loop, call update_open_item. If something important is still unknown, record it as kind "open_question".

{_actions_section(task)}

{_safety_section(asset)}
"""


_ACTIONS = [  # (tools needed, instruction): only lines whose tools this task allows are given to the model
    ({"reserve_spare_part"}, "In-stock part they want: reserve_spare_part."),
    ({"create_procurement_request"}, "Out-of-stock part: offer a procurement request. create_procurement_request only drafts it. Read back part, quantity and work order, then ask \"Shall I submit it?\" and stop talking."),
    ({"approve_procurement_request"}, "Only after the technician clearly says yes, call approve_procurement_request. Never call it in the same turn as the draft. If it returns APPROVAL_REQUIRED, ask again. Say the part is ordered only if verified is true, and give the expected date."),
    ({"update_work_order", "approve_procurement_request"}, "After a verified order, offer to set the work order to WAITING_PARTS with a note."),
    ({"track_shipment"}, "Where a delivery or shipment is: call track_shipment and give status, last scan and ETA from the result."),
    ({"create_stock_transfer"}, "To move stock between locations (for example replenishing a pick face from reserve): check_inventory first, then create_stock_transfer only drafts it. Read back item, quantity, from and to, then ask \"Shall I move it?\" and stop talking."),
    ({"confirm_stock_transfer"}, "Only after the worker clearly says yes, call confirm_stock_transfer. Never call it in the same turn as the draft. Say it is moved and posted to the ERP only if verified is true, and give the ERP reference."),
    ({"get_training_module", "record_training_answer"}, "Training: call get_training_module, say the module title and how many questions, then ask one question at a time. After each answer call record_training_answer with their words; tell them the result it returns and teach the missing point from 'explain' and the manual section. Never mark an answer yourself."),
    ({"finish_training_module"}, "After the last question call finish_training_module and say the score and status exactly as returned. If it needs review, offer to schedule a follow-up session."),
    ({"schedule_follow_up"}, "When something must happen later (a recount, a re-check, a part to fit, a retraining), offer a follow-up and, if they agree, call schedule_follow_up with what, when and who. Say it is scheduled only if verified is true."),
    ({"create_shift_handoff"}, "When asked for the handoff, or at the end of the shift, call create_shift_handoff and speak a two or three sentence version of spoken_summary."),
]


def _actions_section(task: dict[str, Any]) -> str:
    allowed = set(allowed_tools(task))
    lines = [f"- {text}" for need, text in _ACTIONS if need <= allowed]
    if task.get("read_only"):
        lines.append(f"- You cannot order, reserve, move stock, change work orders, escalate or approve anything in a {task['label'].lower()} "
                     "session. If asked, say it is not available in this session and that nothing was changed. Never offer to do it.")
    return "ACTIONS:\n" + "\n".join(lines)


def build_greeting(asset: dict[str, Any], technician: str, task: dict[str, Any]) -> str:
    template = task.get("greeting") or "SHIFTTRACE is live on {asset_name}. {first_name}, how can I help?"
    return template.format(asset_name=asset["name"], asset_id=asset["asset_id"], first_name=technician.split()[0],
                           task=task["label"])


class AgoraSessions:
    def __init__(self) -> None:
        self._client: AsyncAgora | None = None
        self._sessions: dict[str, Any] = {}

    def _get_client(self) -> AsyncAgora:
        if not settings.agora_ready:
            raise RuntimeError("AGORA_APP_ID and AGORA_APP_CERTIFICATE are not set in backend/.env")
        if self._client is None:
            # Agora REST auth: the Customer ID / Customer Secret (RESTful API key) when set, else App ID + certificate tokens.
            auth = ({"customer_id": settings.agora_customer_id, "customer_secret": settings.agora_customer_secret}
                    if settings.agora_customer_id and settings.agora_customer_secret else {})
            self._client = AsyncAgora(area=Area.US, app_id=settings.agora_app_id, app_certificate=settings.agora_app_certificate, **auth)
        return self._client

    def is_running(self, session_id: str) -> bool:
        return session_id in self._sessions

    def build_agent(self, session_id: str, asset: dict[str, Any], technician: str, shift: str,
                    task: dict[str, Any] | None = None) -> AgoraAgent:
        task = task or get_task(None)
        if not settings.murf_ready:
            raise RuntimeError("MURF_API_KEY is not set in backend/.env (Murf Falcon is required for TTS)")
        if not settings.mcp_public_url:
            raise RuntimeError("MCP_PUBLIC_URL is not set: Agora cloud needs a public URL to reach the SHIFTTRACE tools (run the tunnel)")
        mcp_servers = [{
            "name": "shifttrace",
            "endpoint": f"{settings.mcp_public_url}/mcp",
            "transport": "streamable_http",
            "headers": {"Authorization": f"Bearer {settings.mcp_token}", "X-Shifttrace-Session": session_id,
                        "ngrok-skip-browser-warning": "1"},  # harmless elsewhere; avoids ngrok's free-tier interstitial
            "allowed_tools": allowed_tools(task),
            "timeout_ms": 10000,
        }]
        greeting = build_greeting(asset, technician, task)
        llm = OpenAI(
            model=settings.llm_model,
            input_modalities=["text", "image"],
            system_messages=[{"role": "system", "content": build_instructions(asset, technician, shift, task)}],
            greeting_message=greeting,
            failure_message="Sorry, I hit a problem there. Could you say that again?",
            mcp_servers=mcp_servers,
            max_history=40,
        )
        stt = DeepgramSTT(model="nova-3", language="en")
        tts = MurfTTS(
            key=settings.murf_api_key,
            base_url=settings.murf_base_url,
            voice_id=settings.murf_voice_id,
            locale=settings.murf_locale,
            model="FALCON",
            sample_rate=24000,
        )
        agent = AgoraAgent(
            client=self._get_client(),
            greeting=greeting,
            failure_message="Sorry, I hit a problem there. Could you say that again?",
            max_history=40,
            turn_detection={"config": {
                "speech_threshold": 0.5,
                "start_of_speech": {"mode": "vad", "vad_config": {"interrupt_duration_ms": 200, "prefix_padding_ms": 300}},
                "end_of_speech": {"mode": "vad", "vad_config": {"silence_duration_ms": 640}},
            }},
            advanced_features={"enable_rtm": True, "enable_tools": True},
            parameters={"data_channel": "rtm", "enable_error_message": True, "enable_metrics": True, "audio_scenario": "chorus"},
            filler_words=FILLER_WORDS,
        )
        return agent.with_stt(stt).with_llm(llm).with_tts(tts)

    @staticmethod
    def request_preview(session: Any) -> dict[str, Any]:
        """Replay the SDK's own start() request construction (build -> resolve managed presets ->
        validate) without sending it, so the stored audit copy is what Agora receives, minus secrets."""
        try:
            skip, allow = session._vendor_validation_categories(None)  # noqa: SLF001 (SDK internals, audit only)
            token_opts = {"app_id": settings.agora_app_id, "app_certificate": settings.agora_app_certificate, "expires_in": 14400}
            props = session._build_start_properties(token_opts, skip_vendor_validation_categories=skip,  # noqa: SLF001
                                                    allow_missing_vendor_categories=allow)
            preset, resolved = resolve_session_presets(session._preset, props)  # noqa: SLF001
            session._request_properties_for_start(resolved, resolved_preset=preset, pipeline_id=None)  # noqa: SLF001
            out = copy.deepcopy(resolved)
            out["_preset"] = preset
            return out
        except Exception as e:  # surfaces config errors before the network call
            return {"error": f"{type(e).__name__}: {e}"}

    @staticmethod
    def redacted_properties(props: dict[str, Any]) -> dict[str, Any]:
        props = copy.deepcopy(props)

        def scrub(node: Any) -> Any:
            if isinstance(node, dict):
                out = {}
                for k, v in node.items():
                    if k.lower() in {"api_key", "key", "token", "authorization"}:
                        out[k] = "***redacted***" if v else v
                    else:
                        out[k] = scrub(v)
                return out
            if isinstance(node, list):
                return [scrub(x) for x in node]
            return node

        return scrub(props)

    async def start(self, session_id: str, asset: dict[str, Any], technician: str, shift: str,
                    task: dict[str, Any] | None = None, attempts: int = 4, link_timeout_s: float = 9) -> dict[str, Any]:
        """Start an agent and verify Agora actually connected to our MCP tools.

        Live testing (19 Nov) showed ~1 in 4 agents never connected to the tools; those agents also never
        greeted. An agent without tools is unsafe here (it invents results), so we stop it and retry."""
        import asyncio

        from .mcp_server import mcp_links

        last_err = "no attempt"
        for attempt in range(1, attempts + 1):
            t0 = time.monotonic()
            result = await self._start_once(session_id, asset, technician, shift, task)
            while time.monotonic() - t0 < link_timeout_s:
                if mcp_links.get(session_id, 0) >= t0:
                    result["tools_linked_ms"] = int((mcp_links[session_id] - t0) * 1000)
                    result["attempts"] = attempt
                    from . import costs
                    costs.segment_start(session_id, "voice")  # agent minutes are billed from here until stop
                    return result
                await asyncio.sleep(0.25)
            last_err = f"Agora did not connect to the tools within {link_timeout_s:.0f}s (attempt {attempt})"
            log.warning("%s; stopping agent %s and retrying", last_err, result["agent_id"])
            await self.stop(session_id)
        raise RuntimeError(f"{last_err}. Voice agent not started so it cannot answer without its tools.")

    async def _start_once(self, session_id: str, asset: dict[str, Any], technician: str, shift: str,
                          task: dict[str, Any] | None = None) -> dict[str, Any]:
        agent = self.build_agent(session_id, asset, technician, shift, task)
        channel = f"st-{session_id.lower()}-{int(time.time()) % 100000}"
        user_uid = random.randint(1000, 9_999_999)
        agent_uid = random.randint(10_000_000, 99_999_999)
        session = agent.create_async_session(
            channel=channel, agent_uid=str(agent_uid), remote_uids=[str(user_uid)],
            name=f"shifttrace-{session_id.lower()}-{int(time.time())}", idle_timeout=300, enable_string_uid=False,  # ride out venue Wi-Fi blips (agent exited after 120 s in a live test)
           
            expires_in=14400,
        )
        audit = self.redacted_properties(self.request_preview(session))
        started = time.perf_counter()
        agent_id = await session.start()
        log.info("agent started session=%s agent_id=%s channel=%s in %.0f ms", session_id, agent_id, channel,
                 (time.perf_counter() - started) * 1000)
        self._sessions[session_id] = session
        token = generate_client_token(settings.agora_app_id, settings.agora_app_certificate, channel, user_uid, token_expire=14400)
        return {
            "agent_id": agent_id, "channel": channel, "user_uid": user_uid, "agent_uid": agent_uid,
            "app_id": settings.agora_app_id, "token": token, "agent_config": audit,
        }

    async def stop(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        from . import costs
        costs.segment_end(session_id)  # stops the agent and camera meters
        if session is None:
            return False
        try:
            await session.stop()
        except Exception:
            log.warning("agent stop failed for %s", session_id, exc_info=True)
            return False
        return True

    async def info(self, session_id: str) -> dict[str, Any] | None:
        """Agora's view of the agent: status RUNNING / STOPPED / FAILED and an exit message."""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        try:
            r = await session.get_info()
        except Exception as e:
            return {"status": "UNKNOWN", "message": f"{type(e).__name__}"}
        get = (lambda k: r.get(k)) if isinstance(r, dict) else (lambda k: getattr(r, k, None))
        return {"status": str(get("status") or "UNKNOWN"), "message": get("message"), "agent_id": get("agent_id")}

    def forget(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def say(self, session_id: str, text: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        try:
            await session.say(text, priority="APPEND", interruptable=True)
            return True
        except Exception:
            log.warning("agent say failed for %s", session_id, exc_info=True)
            return False

    async def think(self, session_id: str, text: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        try:
            await session.think(text, on_listening_action="inject")
            return True
        except Exception:
            log.warning("agent think failed for %s", session_id, exc_info=True)
            return False


agora_sessions = AgoraSessions()
