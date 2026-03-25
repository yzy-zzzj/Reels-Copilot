"""
Pydantic models for Instagram webhook payloads and the internal Job structure.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any

from pydantic import BaseModel


# ── Instagram webhook payload shapes ──────────────────────────────────────────

class AttachmentPayload(BaseModel):
    url: str | None = None

class Attachment(BaseModel):
    type: str
    payload: AttachmentPayload | None = None

class MessageContent(BaseModel):
    mid: str | None = None
    text: str | None = None
    attachments: list[Attachment] | None = None

class Sender(BaseModel):
    id: str

class Recipient(BaseModel):
    id: str

class MessagingEvent(BaseModel):
    sender: Sender
    recipient: Recipient
    timestamp: int | None = None
    message: MessageContent | None = None

class Entry(BaseModel):
    id: str | None = None
    time: int | None = None
    messaging: list[MessagingEvent] | None = None
    changes: list[Any] | None = None

class WebhookBody(BaseModel):
    object: str
    entry: list[Entry]


# ── Internal job ───────────────────────────────────────────────────────────────

@dataclass
class Job:
    sender_id: str
    reel_url: str
    message_id: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "Job":
        return cls(**json.loads(data))
