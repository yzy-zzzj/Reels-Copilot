"""
Sends a reply to an Instagram user via the Graph API Messaging endpoint.
Handles chunking for Instagram's 1000-character DM limit.
"""
from __future__ import annotations

import logging

import httpx

from app.config import INSTAGRAM_PAGE_ACCESS_TOKEN, GRAPH_API_URL

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 950  # stay safely below Instagram's 1000-char limit


def send_reply(recipient_id: str, text: str) -> None:
    """Send `text` to `recipient_id`, splitting into chunks if needed."""
    chunks = _split(text)
    for i, chunk in enumerate(chunks):
        _post(recipient_id, chunk)
        logger.info("Sent chunk %d/%d to %s", i + 1, len(chunks), recipient_id)


def _split(text: str) -> list[str]:
    if len(text) <= _CHUNK_SIZE:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:_CHUNK_SIZE])
        text = text[_CHUNK_SIZE:]
    return chunks


def _post(recipient_id: str, text: str) -> None:
    url = f"{GRAPH_API_URL}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "access_token": INSTAGRAM_PAGE_ACCESS_TOKEN,
    }
    resp = httpx.post(url, json=payload, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Instagram API error {resp.status_code}: {resp.text}"
        )
