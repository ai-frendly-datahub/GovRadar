from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from govradar.notifier import (
    CompositeNotifier,
    EmailNotifier,
    NotificationPayload,
    WebhookNotifier,
)

pytestmark = pytest.mark.unit


def _payload() -> NotificationPayload:
    return NotificationPayload(
        category_name="govsupport",
        sources_count=3,
        collected_count=10,
        matched_count=7,
        errors_count=1,
        timestamp=datetime(2026, 5, 21, 9, 30, tzinfo=UTC),
        report_url="https://example.com/report",
    )


def test_notification_payload_to_dict_uses_iso_timestamp() -> None:
    data = _payload().to_dict()

    assert data["category_name"] == "govsupport"
    assert data["timestamp"] == "2026-05-21T09:30:00+00:00"
    assert data["report_url"] == "https://example.com/report"


def test_email_notifier_builds_and_sends_message() -> None:
    smtp = Mock()
    smtp_context = Mock()
    smtp_context.__enter__ = Mock(return_value=smtp)
    smtp_context.__exit__ = Mock(return_value=False)

    with patch("govradar.notifier.smtplib.SMTP", return_value=smtp_context) as smtp_ctor:
        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="pass",
            from_addr="from@example.com",
            to_addrs=["to@example.com"],
        )

        assert notifier.send(_payload()) is True

    smtp_ctor.assert_called_once_with("smtp.example.com", 587)
    smtp.starttls.assert_called_once_with()
    smtp.login.assert_called_once_with("user", "pass")
    sent_message = smtp.send_message.call_args.args[0]
    assert sent_message["Subject"] == "Radar Pipeline Complete: govsupport"
    assert "Collected: 10" in sent_message.get_payload()


def test_email_notifier_returns_false_on_smtp_error() -> None:
    with patch("govradar.notifier.smtplib.SMTP", side_effect=OSError("smtp down")):
        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="pass",
            from_addr="from@example.com",
            to_addrs=["to@example.com"],
        )

        assert notifier.send(_payload()) is False


def test_webhook_notifier_posts_payload_and_handles_status() -> None:
    response = Mock(status_code=204)
    with patch("govradar.notifier.requests.post", return_value=response) as post:
        notifier = WebhookNotifier(
            "https://hooks.example.com",
            headers={"X-Test": "1"},
        )

        assert notifier.send(_payload()) is True

    post.assert_called_once()
    assert post.call_args.kwargs["json"]["category_name"] == "govsupport"
    assert post.call_args.kwargs["headers"] == {"X-Test": "1"}


def test_webhook_notifier_get_and_failure_paths() -> None:
    with patch("govradar.notifier.requests.get", return_value=Mock(status_code=200)) as get:
        assert WebhookNotifier("https://hooks.example.com", method="GET").send(_payload()) is True
    get.assert_called_once_with("https://hooks.example.com", headers={}, timeout=10)

    with patch("govradar.notifier.requests.post", return_value=Mock(status_code=500)):
        assert WebhookNotifier("https://hooks.example.com").send(_payload()) is False

    assert WebhookNotifier("https://hooks.example.com", method="PUT").send(_payload()) is False

    with patch("govradar.notifier.requests.post", side_effect=RuntimeError("network")):
        assert WebhookNotifier("https://hooks.example.com").send(_payload()) is False


def test_composite_notifier_aggregates_results_and_exceptions() -> None:
    payload = _payload()
    good = Mock()
    good.send.return_value = True
    bad = Mock()
    bad.send.return_value = False
    broken = Mock()
    broken.send.side_effect = RuntimeError("boom")

    assert CompositeNotifier([]).send(payload) is True
    assert CompositeNotifier([good]).send(payload) is True
    assert CompositeNotifier([good, bad]).send(payload) is False
    assert CompositeNotifier([good, broken]).send(payload) is False
