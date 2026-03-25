"""
Worker main loop.

Run with:
    fwclean/bin/python -m worker.runner

Pulls jobs from Redis, runs the full pipeline, and sends the reply.
Failed jobs (after MAX_RETRIES attempts) are moved to a dead-letter queue.
"""
from __future__ import annotations

import logging
import tempfile

import redis as redis_lib

from app import config
from app.queue import dequeue, move_to_failed
from app.models import Job
from worker.downloader import download_audio
from worker.transcriber import transcribe_file
from worker.analyzer import analyze
from worker.sender import send_reply

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
_RETRY_KEY_PREFIX = "retries:"


def process(job: Job, redis) -> None:
    logger.info("Processing job %s (sender=%s)", job.message_id, job.sender_id)

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = download_audio(job.reel_url, tmp)
        transcript = transcribe_file(audio_path)

    if not transcript.strip():
        send_reply(job.sender_id, "Sorry, I couldn't make out any speech in that video.")
        return

    analysis = analyze(transcript)
    send_reply(job.sender_id, analysis)
    logger.info("Reply sent for job %s", job.message_id)


def run() -> None:
    redis = redis_lib.from_url(config.REDIS_URL, decode_responses=True)
    logger.info("Worker started — waiting for jobs on Redis %s", config.REDIS_URL)

    while True:
        job = dequeue(redis)
        if job is None:
            continue

        retry_key = f"{_RETRY_KEY_PREFIX}{job.message_id}"
        attempts = int(redis.get(retry_key) or 0)

        try:
            process(job, redis)
            redis.delete(retry_key)
        except Exception as exc:
            attempts += 1
            logger.error("Job %s failed (attempt %d): %s", job.message_id, attempts, exc)
            if attempts >= MAX_RETRIES:
                logger.error("Moving job %s to dead-letter queue", job.message_id)
                move_to_failed(job, redis)
                redis.delete(retry_key)
                try:
                    send_reply(
                        job.sender_id,
                        "Sorry, I ran into an error processing that video. Please try again later.",
                    )
                except Exception:
                    pass
            else:
                redis.set(retry_key, attempts, ex=3600)
                # Re-enqueue for retry
                from app.queue import enqueue
                enqueue(job, redis)


if __name__ == "__main__":
    run()
