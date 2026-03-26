"""
Instagram webhook routes: challenge verification + DM event handler.
"""
from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, HTTPException, Query, Request, Response

from app import config
from app.models import WebhookBody, Job
from app.queue import enqueue
from app.validation import check_rate_limit, extract_reel_url, is_spam

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
) -> Response:
    """Instagram calls this to verify the webhook endpoint ownership."""
    if hub_mode == "subscribe" and hub_verify_token == config.INSTAGRAM_VERIFY_TOKEN:
        logger.info("Webhook verified")
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_event(request: Request) -> dict:
    """
    Receives Instagram DM events. Always returns HTTP 200 immediately.
    Heavy processing is handed off to the worker via Redis queue.
    """
    # Validate X-Hub-Signature-256 to confirm the request is from Meta
    raw_body = await request.body()
    _verify_signature(request, raw_body)

    try:
        body = WebhookBody.model_validate_json(raw_body)
    except Exception as exc:
        logger.warning("Failed to parse webhook body: %s", exc)
        return {"status": "ok"}

    if body.object != "instagram":
        return {"status": "ok"}

    redis = request.app.state.redis

    for entry in body.entry:
        for event in (entry.messaging or []):
            _handle_messaging_event(event, redis)

    return {"status": "ok"}


def _handle_messaging_event(event, redis) -> None:
    sender_id = event.sender.id

    if event.message:
        logger.info(
            "Incoming message — text=%r attachments=%r",
            event.message.text,
            [{"type": a.type, "payload": a.payload.model_dump() if a.payload else None}
             for a in (event.message.attachments or [])],
        )

    reel_url = extract_reel_url(event)
    if not reel_url:
        logger.debug("No Reel URL from %s — ignoring", sender_id)
        return

    if is_spam(event, redis):
        logger.info("Spam detected from %s", sender_id)
        return

    if not check_rate_limit(sender_id, redis):
        logger.info("Rate limit exceeded for %s", sender_id)
        return

    mid = event.message.mid if event.message else "unknown"
    job = Job(sender_id=sender_id, reel_url=reel_url, message_id=mid)
    enqueue(job, redis)
    logger.info("Enqueued job %s for sender %s", mid, sender_id)


def _verify_signature(request: Request, body: bytes) -> None:
    """Reject requests that don't carry a valid Meta signature."""
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    if not sig_header.startswith("sha256="):
        raise HTTPException(status_code=400, detail="Missing signature")

    expected = hmac.new(
        config.INSTAGRAM_APP_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(sig_header[len("sha256="):], expected):
        raise HTTPException(status_code=403, detail="Invalid signature")
