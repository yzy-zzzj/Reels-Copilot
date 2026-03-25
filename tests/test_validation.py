"""Tests for the validation layer."""
from unittest.mock import MagicMock
import pytest

from app.models import MessagingEvent, Sender, Recipient, MessageContent, Attachment, AttachmentPayload
from app.validation import extract_reel_url, check_rate_limit, is_spam


def _make_event(text: str | None = None, attachments=None) -> MessagingEvent:
    return MessagingEvent(
        sender=Sender(id="user123"),
        recipient=Recipient(id="page456"),
        message=MessageContent(mid="mid_1", text=text, attachments=attachments),
    )


class TestExtractReelUrl:
    def test_url_in_text(self):
        event = _make_event(text="Check this out https://www.instagram.com/reel/ABC123/ cool right")
        assert extract_reel_url(event) == "https://www.instagram.com/reel/ABC123/"

    def test_reels_plural_url(self):
        event = _make_event(text="https://instagram.com/reels/XYZ789")
        assert extract_reel_url(event) == "https://instagram.com/reels/XYZ789"

    def test_non_reel_url_ignored(self):
        event = _make_event(text="https://instagram.com/p/ABC123")
        assert extract_reel_url(event) is None

    def test_no_message(self):
        event = MessagingEvent(sender=Sender(id="u"), recipient=Recipient(id="p"))
        assert extract_reel_url(event) is None

    def test_attachment_reel(self):
        att = Attachment(type="ig_reel", payload=AttachmentPayload(url="https://www.instagram.com/reel/DEF456/"))
        event = _make_event(attachments=[att])
        assert extract_reel_url(event) == "https://www.instagram.com/reel/DEF456/"

    def test_non_reel_attachment_ignored(self):
        att = Attachment(type="image", payload=AttachmentPayload(url="https://example.com/photo.jpg"))
        event = _make_event(attachments=[att])
        assert extract_reel_url(event) is None


class TestRateLimit:
    def test_within_limit(self):
        redis = MagicMock()
        redis.incr.return_value = 1
        assert check_rate_limit("user1", redis) is True
        redis.expire.assert_called_once()

    def test_at_limit(self):
        redis = MagicMock()
        redis.incr.return_value = 5  # default RATE_LIMIT_MAX=5
        assert check_rate_limit("user1", redis) is True

    def test_over_limit(self):
        redis = MagicMock()
        redis.incr.return_value = 6
        assert check_rate_limit("user1", redis) is False

    def test_expire_only_set_on_first_request(self):
        redis = MagicMock()
        redis.incr.return_value = 3
        check_rate_limit("user1", redis)
        redis.expire.assert_not_called()


class TestIsSpam:
    def test_first_submission_not_spam(self):
        redis = MagicMock()
        redis.exists.return_value = 0
        event = _make_event(text="https://www.instagram.com/reel/ABC123/")
        assert is_spam(event, redis) is False
        redis.set.assert_called_once()

    def test_duplicate_submission_is_spam(self):
        redis = MagicMock()
        redis.exists.return_value = 1
        event = _make_event(text="https://www.instagram.com/reel/ABC123/")
        assert is_spam(event, redis) is True

    def test_no_url_not_spam(self):
        redis = MagicMock()
        event = _make_event(text="hello!")
        assert is_spam(event, redis) is False
