"""
Redis-backed job queue using RPUSH / BLPOP.
"""
from __future__ import annotations

from redis import Redis

from app.models import Job

QUEUE_NAME = "jobs_queue"
FAILED_QUEUE_NAME = "jobs_failed"


def enqueue(job: Job, redis: Redis) -> None:
    redis.rpush(QUEUE_NAME, job.to_json())


def dequeue(redis: Redis, timeout: int = 5) -> Job | None:
    """Block up to `timeout` seconds for a job. Returns None on timeout."""
    result = redis.blpop(QUEUE_NAME, timeout=timeout)
    if result is None:
        return None
    _, raw = result
    return Job.from_json(raw)


def move_to_failed(job: Job, redis: Redis) -> None:
    redis.rpush(FAILED_QUEUE_NAME, job.to_json())
