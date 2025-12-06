"""
Fixed FastAPI server with proper request synchronization and state locking.

Key fixes:
1. Added asyncio locks per session to prevent race conditions
2. Request queuing to ensure sequential processing
3. Better error handling and cleanup
4. Processing state tracking
"""

import base64
import logging
import tempfile
import asyncio
from pathlib import Path
from typing import Optional
from collections import defaultdict

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import Config
from modules.stt import SpeechToText
from modules.tts import TextToSpeech
from modules.llm import MedicalConversationAgent, ConversationState

logger = logging.getLogger("server")


class AppCore:
    """Holds shared components and per-session conversation state with locking."""

    def __init__(self):
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.llm = MedicalConversationAgent()
        self.sessions: dict[str, ConversationState] = {}

        # FIX #1: Add locks per session to prevent race conditions
        self.session_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

        # FIX #2: Track processing status per session
        self.processing: dict[str, bool] = defaultdict(bool)

    async def get_state(self, session_id: Optional[str]) -> tuple[str, ConversationState]:
        """Get or create conversation state for a session (NOT thread-safe by itself)."""
        if session_id and session_id in self.sessions:
            return session_id, self.sessions[session_id]

        # Create a new session
        new_id = session_id or self._generate_session_id()
        state = ConversationState()

        # Initialize with greeting from LLM for consistency
        greeting, state = self.llm.start_conversation()
        state.add_turn("assistant", greeting)
        self.sessions[new_id] = state

        return new_id, state

    async def get_session_lock(self, session_id: str) -> asyncio.Lock:
        """Get the lock for a specific session."""
        return self.session_locks[session_id]

    async def is_session_processing(self, session_id: str) -> bool:
        """Check if a session is currently processing a request."""
        return self.processing.get(session_id, False)

    async def set_processing(self, session_id: str, is_processing: bool):
        """Set processing status for a session."""
        self.processing[session_id] = is_processing

    @staticmethod
    def _generate_session_id() -> str:
        import uuid
        return uuid.uuid4().hex


core = AppCore()
app = FastAPI(title="Voice Agent API (Fixed)", version="1.1.0")
app.mount("/web", StaticFiles(directory="web", html=True), name="web")


@app.get("/api/health")
def health():
    return {"status": "ok"}


# FIX #3: Add endpoint to check if session is processing
@app.get("/api/session/{session_id}/status")
async def session_status(session_id: str):
    """Check if a session is currently processing a request."""
    is_busy = await core.is_session_processing(session_id)
    return {
        "session_id": session_id,
        "is_processing": is_busy,
        "has_state": session_id in core.sessions
    }


def _get_ffmpeg_path() -> Optional[str]:
    """Try to locate an ffmpeg binary."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    import shutil
    return shutil.which("ffmpeg")


def _convert_to_wav_if_needed(input_path: Path, mime_type: Optional[str] = None) -> Path:
    """Ensure the audio is in wav format for STT."""
    suffix = input_path.suffix.lower()
    if suffix == ".wav":
        return input_path

    import subprocess

    ffmpeg_path = _get_ffmpeg_path()
    if ffmpeg_path is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Audio is not WAV and ffmpeg is not available. "
                "Install ffmpeg or use a browser that records WAV."
            ),
        )

    output_path = Path(tempfile.mktemp(suffix=".wav"))

    input_format_args = []
    if mime_type:
        if "ogg" in mime_type:
            input_format_args = ["-f", "ogg"]
        elif "webm" in mime_type:
            input_format_args = ["-f", "webm"]
    if not input_format_args:
        if suffix in [".ogg", ".oga"]:
            input_format_args = ["-f", "ogg"]
        elif suffix == ".webm":
            input_format_args = ["-f", "webm"]

    cmd = [
        ffmpeg_path,
        "-loglevel",
        "error",
        "-y",
        *input_format_args,
        "-i",
        str(input_path),
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        detail_msg = "Failed to convert audio to WAV"
        if e.stderr:
            detail_msg += f": {e.stderr.strip()}"
        raise HTTPException(status_code=500, detail=detail_msg) from e


@app.post("/api/voice")
async def voice(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(default=None),
    mime_type: Optional[str] = Form(default=None),
):
    """
    Accept an audio file, return transcript, agent reply text, and reply audio.

    FIX: Now properly locks per session to prevent race conditions.
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    tmp_path = None
    converted_path = None
    tts_result = None

    # Save upload to a temp file
    try:
        suffix = Path(audio.filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = Path(tmp.name)
            content = await audio.read()
            tmp.write(content)
            tmp.flush()

        if tmp_path.stat().st_size < 200:
            raise HTTPException(status_code=400, detail="Audio chunk was too small/empty")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save uploaded audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to read audio upload")

    try:
        # Convert if needed
        converted_path = _convert_to_wav_if_needed(tmp_path, mime_type)

        # FIX #4: Get or create session WITHOUT lock first (to avoid deadlock on new sessions)
        sid, _ = await core.get_state(session_id)

        # FIX #5: Acquire session lock to ensure sequential processing
        async with await core.get_session_lock(sid):
            # Mark session as processing
            await core.set_processing(sid, True)

            try:
                # Get current state inside lock
                _, state = await core.get_state(sid)

                # Transcribe
                logger.info(f"[Session {sid}] Transcribing audio...")
                transcript = core.stt.transcribe(converted_path)
                user_text = (transcript.get("text") or "").strip()

                if not user_text:
                    logger.info(f"[Session {sid}] Empty transcription, returning silence")
                    return JSONResponse(
                        {
                            "session_id": sid,
                            "user_text": "",
                            "reply_text": "",
                            "reply_audio_b64": "",
                            "sample_rate": core.tts.sample_rate,
                            "silence": True,
                        },
                        status_code=200,
                    )

                logger.info(f"[Session {sid}] User said: '{user_text}'")

                # Generate agent reply
                logger.info(f"[Session {sid}] Generating LLM response...")
                reply_text = core.llm.generate_response(user_text, state)
                logger.info(f"[Session {sid}] Agent reply: '{reply_text}'")

                # Synthesize reply audio
                logger.info(f"[Session {sid}] Synthesizing TTS...")
                audio_output_path = Path(tempfile.mktemp(suffix=".wav"))
                tts_result = core.tts.synthesize(
                    reply_text,
                    output_path=audio_output_path,
                    auto_play=False,
                    save_audio=True,
                )

                # Read synthesized audio bytes and encode
                with open(tts_result["audio_path"], "rb") as f:
                    reply_audio_bytes = f.read()

                reply_audio_b64 = base64.b64encode(reply_audio_bytes).decode("ascii")

                response_body = {
                    "session_id": sid,
                    "user_text": user_text,
                    "reply_text": reply_text,
                    "reply_audio_b64": reply_audio_b64,
                    "sample_rate": core.tts.sample_rate,
                }

                logger.info(f"[Session {sid}] Request completed successfully")
                return JSONResponse(response_body)

            finally:
                # Always mark session as done processing
                await core.set_processing(sid, False)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")

    finally:
        # Cleanup temp files
        try:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup tmp_path: {e}")

        try:
            if converted_path and converted_path != tmp_path and converted_path.exists():
                converted_path.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup converted_path: {e}")

        try:
            if tts_result and tts_result.get("audio_path"):
                audio_path = Path(tts_result["audio_path"])
                if audio_path.exists():
                    audio_path.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup tts audio: {e}")
