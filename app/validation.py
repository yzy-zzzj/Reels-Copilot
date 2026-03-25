"""
Validation layer: URL extraction, rate limiting, spam detection.
"""
from __future__ import annotations

import re
from redis import Redis

from app.config import RATE_LIMIT_MAX, RATE_LIMIT_WINDOW
from app.models import MessagingEvent

# Matches instagram.com/reel/<id> and instagram.com/reels/<id>
_REEL_PATTERN = re.compile(
    r"https?://(?:www\.)?instagram\.com/reels?/[A-Za-z0-9_-]+/?(?:\?[^\s]*)?"
)


def extract_reel_url(event: MessagingEvent) -> str | None:
    """Return the first Instagram Reel URL from a messaging event, or None."""
    msg = event.message
    if not msg:
        return None

    # Check text body
    if msg.text:
        match = _REEL_PATTERN.search(msg.text)
        if match:
            return match.group(0)

    # Check attachments (user shared/forwarded a Reel)
    if msg.attachments:
        for att in msg.attachments:
            if att.type in ("ig_reel", "video", "share") and att.payload and att.payload.url:
                if _REEL_PATTERN.search(att.payload.url):
                    return att.payload.url

    return None


def check_rate_limit(sender_id: str, redis: Redis) -> bool:
    """
    Returns True if the sender is within the allowed rate limit.
    Uses Redis INCR + EXPIRE with a sliding window.
    """
    key = f"rl:{sender_id}"
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, RATE_LIMIT_WINDOW)
    return count <= RATE_LIMIT_MAX


def is_spam(event: MessagingEvent, redis: Redis) -> bool:
    """
    Lightweight spam check: reject if the exact same URL was already submitted
    by this sender within the last 60 seconds.
    """
    msg = event.message
    if not msg or not msg.text:
        return False

    url = extract_reel_url(event)
    if not url:
        return False

    key = f"spam:{event.sender.id}:{url}"
    if redis.exists(key):
        return True
    redis.set(key, 1, ex=60)
    return False
