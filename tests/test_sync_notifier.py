"""Tests for sync notifier (notifier.py)."""

import pytest
from unittest.mock import patch, MagicMock
from skill_seekers.sync.notifier import Notifier
from skill_seekers.sync.models import WebhookPayload, ChangeReport, PageChange, ChangeType


@pytest.fixture
def sample_payload():
    return WebhookPayload(
        event="change_detected",
        skill_name="test-skill",
        metadata={"source": "test"},
    )


@pytest.fixture
def changed_payload():
    report = ChangeReport(
        skill_name="test-skill",
        total_pages=5,
        added=[PageChange(url="https://new.page", change_type=ChangeType.ADDED)],
        modified=[
            PageChange(
                url="https://mod.page", change_type=ChangeType.MODIFIED, old_hash="a", new_hash="b"
            )
        ],
        deleted=[PageChange(url="https://del.page", change_type=ChangeType.DELETED)],
    )
    return WebhookPayload(event="change_detected", skill_name="test-skill", changes=report)


class TestNotifier:
    def test_init_defaults(self):
        n = Notifier()
        assert n.console is True
        assert n.webhook_url is None
        assert n.slack_webhook is None
        assert n.email_recipients == []

    def test_init_with_urls(self):
        n = Notifier(
            webhook_url="https://hooks.example.com", slack_webhook="https://hooks.slack.com/xxx"
        )
        assert n.webhook_url == "https://hooks.example.com"
        assert n.slack_webhook == "https://hooks.slack.com/xxx"

    def test_init_with_email(self):
        n = Notifier(email_recipients=["a@b.com", "c@d.com"])
        assert len(n.email_recipients) == 2

    def test_init_console_disabled(self):
        n = Notifier(console=False)
        assert n.console is False

    def test_send_console_routes(self, sample_payload, capsys):
        n = Notifier(webhook_url=None, slack_webhook=None, console=True)
        n._send_console(sample_payload)
        captured = capsys.readouterr()
        assert "CHANGE_DETECTED" in captured.out
        assert "test-skill" in captured.out

    def test_send_console_with_changes(self, changed_payload, capsys):
        n = Notifier()
        n._send_console(changed_payload)
        captured = capsys.readouterr()
        assert "Added: 1" in captured.out
        assert "Modified: 1" in captured.out
        assert "Deleted: 1" in captured.out

    def test_send_console_no_changes(self, capsys):
        report = ChangeReport(skill_name="test-skill", total_pages=5, unchanged=5)
        payload = WebhookPayload(event="change_detected", skill_name="test-skill", changes=report)
        n = Notifier()
        n._send_console(payload)
        captured = capsys.readouterr()
        assert "No changes detected" in captured.out

    @patch("skill_seekers.sync.notifier.requests.post")
    def test_send_webhook(self, mock_post, sample_payload):
        mock_post.return_value.raise_for_status = MagicMock()
        n = Notifier(webhook_url="https://hooks.example.com/webhook")
        n._send_webhook(sample_payload)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://hooks.example.com/webhook"
        assert kwargs["json"]["event"] == "change_detected"

    @patch("skill_seekers.sync.notifier.requests.post")
    def test_send_webhook_http_error(self, mock_post, sample_payload):
        mock_post.side_effect = Exception("Connection refused")
        n = Notifier(webhook_url="https://hooks.example.com/webhook")
        n._send_webhook(sample_payload)

    @patch("skill_seekers.sync.notifier.requests.post")
    def test_send_slack(self, mock_post, changed_payload):
        mock_post.return_value.raise_for_status = MagicMock()
        n = Notifier(slack_webhook="https://hooks.slack.com/xxx")
        n._send_slack(changed_payload)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://hooks.slack.com/xxx"
        assert "text" in kwargs["json"]

    @patch("skill_seekers.sync.notifier.requests.post")
    def test_send_slack_many_modified(self, mock_post, capsys):
        modified = [
            PageChange(
                url=f"https://page{i}.com",
                change_type=ChangeType.MODIFIED,
                old_hash="a",
                new_hash="b",
            )
            for i in range(10)
        ]
        report = ChangeReport(skill_name="test-skill", total_pages=10, modified=modified)
        payload = WebhookPayload(event="change_detected", skill_name="test-skill", changes=report)
        n = Notifier(slack_webhook="https://hooks.slack.com/xxx")
        n._send_slack(payload)
        call_arg = mock_post.call_args[1]["json"]["text"]
        assert "...and 5 more" in call_arg

    def test_send_skips_disabled_channels(self, sample_payload, capsys):
        n = Notifier(webhook_url=None, slack_webhook=None, email_recipients=[], console=False)
        n.send(sample_payload)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_send_uses_all_channels(self, sample_payload, capsys):
        with (
            patch.object(Notifier, "_send_webhook") as mock_webhook,
            patch.object(Notifier, "_send_slack") as mock_slack,
            patch.object(Notifier, "_send_email") as mock_email,
        ):
            n = Notifier(
                webhook_url="https://hooks.example.com",
                slack_webhook="https://hooks.slack.com/xxx",
                email_recipients=["dev@example.com"],
                console=True,
            )
            n.send(sample_payload)
            mock_webhook.assert_called_once()
            mock_slack.assert_called_once()
            mock_email.assert_called_once()
