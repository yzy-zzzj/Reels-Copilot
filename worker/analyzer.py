"""
Sends a transcript to Claude for fact-checking analysis.
The Anthropic client is created once at module level.
"""
from __future__ import annotations

import logging
from pathlib import Path

import anthropic

from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_SYSTEM_PROMPT = (Path(__file__).parent.parent / "prompts" / "factcheck.txt").read_text()


def analyze(transcript: str) -> str:
    """
    Run the fact-checking prompt against `transcript`.
    Returns the assistant's reply as a plain string.
    """
    logger.info("Sending transcript to Claude (%d chars)", len(transcript))

    response = _client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Transcript:\n\n{transcript}"}
        ],
    )

    return response.content[0].text
