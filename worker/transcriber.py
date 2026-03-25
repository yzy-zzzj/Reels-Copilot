"""
Transcribes an audio file using faster-whisper.
The WhisperModel is loaded once at module level to avoid per-job reload overhead.
"""
from __future__ import annotations

import logging

from faster_whisper import WhisperModel

from app.config import WHISPER_MODEL

logger = logging.getLogger(__name__)

# Load model once when the worker starts
_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
logger.info("WhisperModel loaded: %s", WHISPER_MODEL)


def transcribe_file(path: str, language: str | None = None) -> str:
    """
    Transcribe the audio at `path` and return the full text as a single string.
    """
    segments, info = _model.transcribe(path, language=language)
    logger.info("Detected language: %s", info.language)

    parts = [s.text.strip() for s in segments]
    return " ".join(parts)
