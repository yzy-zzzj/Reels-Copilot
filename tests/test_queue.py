"""Tests for the Redis queue helpers (round-trip serialisation)."""
from unittest.mock import MagicMock, call

from app.models import Job
from app.queue import enqueue, dequeue, move_to_failed, QUEUE_NAME, FAILED_QUEUE_NAME


def _make_job() -> Job:
    return Job(sender_id="user1", reel_url="https://instagram.com/reel/ABC", message_id="mid1")


def test_enqueue_calls_rpush():
    redis = MagicMock()
    job = _make_job()
    enqueue(job, redis)
    redis.rpush.assert_called_once_with(QUEUE_NAME, job.to_json())


def test_dequeue_returns_job():
    redis = MagicMock()
    job = _make_job()
    redis.blpop.return_value = (QUEUE_NAME, job.to_json())
    result = dequeue(redis)
    assert result == job


def test_dequeue_returns_none_on_timeout():
    redis = MagicMock()
    redis.blpop.return_value = None
    assert dequeue(redis) is None


def test_move_to_failed():
    redis = MagicMock()
    job = _make_job()
    move_to_failed(job, redis)
    redis.rpush.assert_called_once_with(FAILED_QUEUE_NAME, job.to_json())


def test_job_roundtrip():
    job = _make_job()
    assert Job.from_json(job.to_json()) == job
