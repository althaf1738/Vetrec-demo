from __future__ import annotations
import os
from typing import Optional
from faster_whisper import WhisperModel

# Load once and keep hot in memory
_MODEL: Optional[WhisperModel] = None

def _get_model() -> WhisperModel:
    global _MODEL
    if _MODEL is None:
        model_name = os.getenv("WHISPER_MODEL", "tiny.en")  # tiny.en | base.en | small.en
        # int8 is fastest on CPU / Apple Silicon for demos
        _MODEL = WhisperModel(model_name, compute_type="int8")
    return _MODEL

def transcribe_sync(audio_path: str) -> str:
    """
    Transcribe audio file to text. Returns "" if nothing recognized.
    """
    model = _get_model()
    segments, info = model.transcribe(
        audio_path,
        beam_size=1,
        vad_filter=True,          # voice activity detection to skip silence
        vad_parameters={"min_silence_duration_ms": 300},
    )
    parts = []
    for seg in segments:
        if seg.text:
            parts.append(seg.text.strip())
    return " ".join(parts).strip()

# Async wrapper so we don't block the event loop
import asyncio
async def transcribe_async(audio_path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, transcribe_sync, audio_path)
