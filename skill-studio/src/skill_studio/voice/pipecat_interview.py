"""
Voice-mode interview. Reuses the shared interview loop; Pipecat is just the I/O channel.

Wiring:
- pipecat-preflight validates preset + API keys + kills stale procs
- create_daily_room provisions (or reuses) a room via the Daily REST API
- webbrowser_open auto-opens the URL so the user doesn't hunt for it
- run_pipeline spins the Pipecat pipeline: Daily transport -> Groq Whisper STT -> interview loop -> Deepgram TTS -> Daily transport
"""
from __future__ import annotations
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

from skill_studio.llm_provider import get_provider
from skill_studio.interview.loop import run_interview_turn
from skill_studio.interview.modes import QUESTION_BUDGET
from skill_studio.presets import load_preset
from skill_studio.sops_helper import decrypt_dotenv
from skill_studio.storage import SessionStorage
from skill_studio import paths


DEFAULT_ENV = paths.pipecat_env_file()
SKILL_ENV = paths.env_file()
SESSION_ROOT = paths.session_root()


def webbrowser_open(url: str) -> None:
    webbrowser.open(url)


def run_preflight() -> bool:
    """Invoke pipecat-preflight if present as a CLI; otherwise do minimal inline checks.

    pipecat-preflight in this vault is a Claude Code skill (not a PATH binary), so in
    most invocation contexts we fall back to basic validation.
    """
    try:
        result = subprocess.run(["pipecat-preflight"], capture_output=True, text=True)
    except FileNotFoundError:
        # Inline fallback: check the env files we need exist.
        missing = []
        if not DEFAULT_ENV.exists():
            missing.append(str(DEFAULT_ENV))
        if missing:
            print(f"preflight: missing env files: {', '.join(missing)}")
            return False
        print("preflight: pipecat-preflight not on PATH; using inline check (ok)")
        return True
    if result.returncode != 0:
        if result.stdout:
            print(f"preflight stdout:\n{result.stdout}")
        if result.stderr:
            print(f"preflight stderr:\n{result.stderr}")
    return result.returncode == 0


def create_daily_room() -> str:
    """Create a Daily room via REST API. Returns the room URL."""
    import urllib.request
    import json
    env = decrypt_dotenv(DEFAULT_ENV)
    req = urllib.request.Request(
        "https://api.daily.co/v1/rooms",
        data=b"{}",
        headers={
            "Authorization": f"Bearer {env['DAILY_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return data["url"]


# ---------------------------------------------------------------------------
# InterviewProcessor — sits between STT and TTS in the pipeline
# ---------------------------------------------------------------------------

from pipecat.frames.frames import Frame, TranscriptionFrame, TextFrame, TTSSpeakFrame, EndFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from loguru import logger


class FrameLogger(FrameProcessor):
    """Logs every frame passing through. Use to diagnose where the pipeline stalls."""

    def __init__(self, label: str):
        super().__init__()
        self._label = label
        self._audio_count = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        name = type(frame).__name__
        if "Audio" in name:
            self._audio_count += 1
            if self._audio_count % 50 == 1:  # log every 50th audio frame
                logger.info(f"[{self._label}] {name} (count={self._audio_count})")
        else:
            logger.info(f"[{self._label}] {name}")
        await self.push_frame(frame, direction)


VOICE_COMMANDS = {
    "go_deeper": {"tell me more", "go deeper", "more on that", "elaborate", "say more"},
    "skip":      {"skip", "next", "move on", "next question", "skip this"},
    "stop":      {"done", "wrap up", "stop", "we're done", "that's enough"},
}


def _match_voice_command(text: str) -> str | None:
    """Return the command name if the user's phrase matches a known voice command, else None."""
    t = text.strip().lower().rstrip(".!?")
    for cmd, phrases in VOICE_COMMANDS.items():
        if t in phrases:
            return cmd
    return None


class InterviewProcessor(FrameProcessor):
    """On each TranscriptionFrame → run one interview turn → emit a TTSSpeakFrame with the next question.

    Recognizes voice commands: "tell me more" / "go deeper" (force a follow-up on
    the current subject), "skip" / "next" (advance), "done" / "stop" (close out).
    """

    def __init__(self, design, preset, interviewer, storage):
        super().__init__()
        self._design = design
        self._preset = preset
        self._interviewer = interviewer
        self._storage = storage

    def _run_turn_sync(self, user_input: str | None) -> str:
        """Blocking work that runs off the event loop (LLM calls + disk writes)."""
        question = run_interview_turn(
            self._design, self._preset, self._interviewer, user_input=user_input
        )
        self._storage.save(self._design)
        return question

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame) and frame.text.strip():
            import asyncio

            user_text = frame.text.strip()
            logger.info(f"[interview] user said: {user_text!r}")
            self._storage.append_transcript(self._design.meta.id, "user", user_text)

            cmd = _match_voice_command(user_text)
            if cmd == "stop":
                logger.info("[interview] voice command: stop → closing session")
                await self.push_frame(
                    TTSSpeakFrame("Okay, wrapping up. Your design will be ready in a moment."),
                    FrameDirection.DOWNSTREAM,
                )
                await self.push_frame(EndFrame(), FrameDirection.DOWNSTREAM)
                return

            if cmd == "skip":
                logger.info("[interview] voice command: skip → marking current subject landed")
                from skill_studio.interview.director import DirectorState
                state = DirectorState.from_schema_state(self._design.interview_state)
                if state.current_subject:
                    state.subjects_landed.add(state.current_subject.key)
                    state.follow_ups_on_current = state.max_follow_ups
                self._design.interview_state = state.to_schema_state()
                turn_input = None
            elif cmd == "go_deeper":
                logger.info("[interview] voice command: go_deeper → forcing follow-up")
                turn_input = None
            else:
                turn_input = user_text

            # CRITICAL: run_interview_turn makes blocking LLM calls. If we await it
            # directly inside process_frame, the asyncio loop is frozen for 1-5s,
            # upstream audio frames can't be pumped, and STT starves. Offload it.
            try:
                question = await asyncio.to_thread(self._run_turn_sync, turn_input)
            except Exception as e:
                logger.error(f"[interview] turn failed: {e}")
                question = "Sorry, I lost my train of thought. Could you repeat that?"

            logger.info(f"[interview] next question: {question!r}")
            self._storage.append_transcript(self._design.meta.id, "assistant", question)
            await self.push_frame(TTSSpeakFrame(question), FrameDirection.DOWNSTREAM)
            return  # swallow the TranscriptionFrame

        await self.push_frame(frame, direction)


# ---------------------------------------------------------------------------
# run_pipeline — real Pipecat wiring
# ---------------------------------------------------------------------------

def _enable_debug_logging() -> None:
    """Surface pipecat's per-frame debug output. Set SKILL_STUDIO_QUIET=1 to suppress."""
    import sys
    from loguru import logger as _logger
    if os.environ.get("SKILL_STUDIO_QUIET"):
        return
    _logger.remove()
    _logger.add(sys.stderr, level="DEBUG")


_DEPTH_BLURB = {
    "sprint":   "We'll keep it tight — maybe five to seven questions",
    "standard": "Plan for fifteen or twenty questions, but we can stop anytime",
    "deep":     "This one goes deep — twenty-five plus questions if you're game",
}

_PRESET_BLURB = {
    "ai-agent":        "an AI agent or skill",
    "life-automation": "a life-automation",
    "knowledge-work":  "a knowledge-work tool",
    "custom":          "what you want to build",
}


def _build_greeting(design, next_question: str, resumed: bool) -> str:
    """Craft the first utterance — preset-aware, depth-aware, and acknowledges resumed context.

    Commands the user can always say: "tell me more", "skip", "done".
    """
    depth = getattr(design.meta.interview_mode, "depth", "standard")
    preset = getattr(design.meta, "preset", "custom")
    depth_blurb = _DEPTH_BLURB.get(depth, _DEPTH_BLURB["standard"])
    preset_blurb = _PRESET_BLURB.get(preset, _PRESET_BLURB["custom"])

    if resumed:
        # Name the specific thing the user was working on (if known), mention
        # concrete progress (fields already filled), keep the resume short.
        landed = []
        if getattr(design.problem, "what_hurts", ""):
            landed.append("what hurts")
        if getattr(design.jtbd, "situation", ""):
            landed.append("the moment it happens")
        if design.scenarios:
            landed.append("a specific scenario")
        progress = f"We've already got {', '.join(landed)} down. " if landed else ""
        if design.hook:
            return (
                f"Welcome back. You were sketching {design.hook[:100]}. "
                f"{progress}Let's pick up where we left off. {next_question}"
            )
        return (
            f"Welcome back. {progress}Let's pick up where we left off. {next_question}"
        )

    return (
        f"Hey — I'll help you design {preset_blurb}. "
        f"{depth_blurb}. Answer in whatever detail feels natural; "
        f"say 'tell me more' if you want me to probe, 'skip' to move on, 'done' to wrap up. "
        f"First one: {next_question}"
    )


def run_pipeline(design, preset, interviewer, storage, room_url: str, resumed: bool = False) -> None:
    """Run the Pipecat pipeline until user says 'done' or disconnects.

    Pipeline:
        DailyTransport input
        → GroqSTTService (Whisper large-v3, auto language detection)
        → InterviewProcessor (custom frame processor calling run_interview_turn)
        → DeepgramTTSService (WebSocket streaming)
        → DailyTransport output

    Pipecat version: 1.0.0 (NOT 0.0.50 as originally specified — API differs).
    Import paths used:
        - pipecat.transports.daily.transport.DailyTransport / DailyParams
        - pipecat.services.groq.stt.GroqSTTService  (was WhisperSTTService in spec)
        - pipecat.services.deepgram.tts.DeepgramTTSService
        - pipecat.audio.vad.silero.SileroVADAnalyzer  (was pipecat.vad.silero in spec)
        - PipelineParams has no allow_interruptions field in 1.0.0 — dropped
    """
    _enable_debug_logging()
    import asyncio
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineTask, PipelineParams
    from pipecat.services.groq.stt import GroqSTTService
    from pipecat.services.deepgram.tts import DeepgramTTSService
    from pipecat.transports.daily.transport import DailyTransport, DailyParams
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.audio.vad.vad_analyzer import VADParams
    from pipecat.processors.audio.vad_processor import VADProcessor

    async def _main():
        transport = DailyTransport(
            room_url=room_url,
            token=None,
            bot_name="Skill Studio",
            params=DailyParams(
                audio_in_enabled=True,
                audio_in_sample_rate=16000,   # Whisper prefers 16k
                audio_out_enabled=True,
                audio_out_sample_rate=24000,  # Deepgram Aura native
                transcription_enabled=False,  # we use Groq Whisper instead
                microphone_out_enabled=True,
                camera_out_enabled=False,
                # VAD goes in the pipeline as VADProcessor below — not a DailyParams kwarg
                # (Pipecat 1.0 silently drops unknown kwargs, which bit us hard)
            ),
        )

        stt = GroqSTTService(
            api_key=os.environ["GROQ_API_KEY"],
            model="whisper-large-v3",
        )

        tts = DeepgramTTSService(
            api_key=os.environ["DEEPGRAM_API_KEY"],
            voice=os.environ.get("DEEPGRAM_VOICE", "aura-asteria-en"),
            sample_rate=24000,
        )

        interview = InterviewProcessor(design, preset, interviewer, storage)

        vad = VADProcessor(
            vad_analyzer=SileroVADAnalyzer(
                sample_rate=16000,
                params=VADParams(
                    confidence=0.5,
                    min_volume=0.15,
                    start_secs=0.2,
                    stop_secs=0.6,
                ),
            ),
        )

        pipeline = Pipeline([
            transport.input(),
            FrameLogger("after-transport-in"),
            vad,
            FrameLogger("after-vad"),
            stt,
            FrameLogger("after-stt"),
            interview,
            tts,
            transport.output(),
        ])

        task = PipelineTask(
            pipeline,
            params=PipelineParams(enable_metrics=False),
        )

        @transport.event_handler("on_first_participant_joined")
        async def on_join(transport, participant):
            import asyncio
            logger.info(f"[transport] participant joined: {participant.get('info', {}).get('userName') if isinstance(participant, dict) else participant}")
            # Blocking LLM call — offload to a thread so the event loop stays responsive.
            next_q = await asyncio.to_thread(
                run_interview_turn, design, preset, interviewer, None
            )
            greeting = _build_greeting(design, next_q, resumed=resumed)
            logger.info(f"[interview] greeting: {greeting!r}")
            storage.append_transcript(design.meta.id, "assistant", greeting)
            storage.save(design)
            await task.queue_frames([TTSSpeakFrame(greeting)])

        @transport.event_handler("on_participant_left")
        async def on_leave(transport, participant, reason):
            logger.info(f"[transport] participant left: {reason}")
            # Auto-export artifacts
            try:
                from skill_studio.exporters.registry import get_exporter
                from skill_studio.synthesis import write_session_summary
                from skill_studio.cli import SESSION_ROOT as _SR
                exporter = get_exporter("md-svg")
                session_dir = _SR / design.meta.id
                paths = exporter.render(design, session_dir)
                for p in paths:
                    logger.info(f"[export] {p}")
                # Synthesis + groundwork feed
                tail = [{"role": t.role, "text": t.text} for t in design.transcript]
                write_session_summary(design, tail, interviewer, session_dir)
            except Exception as e:
                logger.error(f"auto-export failed: {e}")
            await task.queue_frames([EndFrame()])

        runner = PipelineRunner()
        try:
            await runner.run(task)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("[pipeline] interrupted (Ctrl+C) — running graceful cleanup")
            # Same shape as the on_participant_left handler — export artifacts + synth.
            try:
                from skill_studio.exporters.registry import get_exporter
                from skill_studio.synthesis import write_session_summary
                from skill_studio.cli import SESSION_ROOT as _SR
                exporter = get_exporter("md-svg")
                session_dir = _SR / design.meta.id
                paths = exporter.render(design, session_dir)
                for p in paths:
                    logger.info(f"[export] {p}")
                tail = [{"role": t.role, "text": t.text} for t in design.transcript]
                write_session_summary(design, tail, interviewer, session_dir)
                print(f"\n✓ Session saved. Resume with: skill-studio new --voice --resume {design.meta.id}")
            except Exception as e:
                logger.error(f"graceful cleanup failed: {e}")
            raise

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        # Swallow so the shell doesn't show a traceback after our graceful export.
        pass


def run_voice_interview(args: Any) -> int:
    if not run_preflight():
        print("pipecat-preflight failed. Fix errors and retry.")
        return 1

    storage = SessionStorage(SESSION_ROOT)
    from skill_studio.cli import resolve_session
    # Voice mode defaults to the conversational style unless the user explicitly
    # picked another — reflection + probing is what makes voice feel human.
    if getattr(args, "style", None) in (None, "scenario-first"):
        args.style = "conversational"
    design, resumed = resolve_session(args, storage)
    preset = load_preset(design.meta.preset)
    if resumed:
        from skill_studio.interview.coverage import overall_coverage
        cov = overall_coverage(design, preset)
        print(f"Resuming session {design.meta.id[:8]} ({cov:.0%} covered)")
    else:
        print(f"New session {design.meta.id[:8]} — style={design.meta.interview_mode.style}")


    os.environ.update(decrypt_dotenv(DEFAULT_ENV))
    if SKILL_ENV.exists():
        os.environ.update(decrypt_dotenv(SKILL_ENV))
    interviewer = get_provider(system_prompt=preset.opening_question)

    room = create_daily_room()
    print(f"Daily room: {room}")
    webbrowser_open(room)

    try:
        run_pipeline(design, preset, interviewer, storage, room_url=room, resumed=resumed)
    except NotImplementedError:
        print("\n[voice pipeline not yet wired — see src/skill_studio/voice/pipecat_interview.py::run_pipeline]")
        return 2
    return 0
