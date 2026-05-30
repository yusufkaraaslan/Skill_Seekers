"""Tests for sync Pydantic models (models.py)."""

from datetime import datetime
from skill_seekers.sync.models import (
    ChangeType,
    PageChange,
    ChangeReport,
    SyncConfig,
    SyncState,
    WebhookPayload,
)


class TestChangeType:
    def test_values(self):
        assert ChangeType.ADDED == "added"
        assert ChangeType.MODIFIED == "modified"
        assert ChangeType.DELETED == "deleted"
        assert ChangeType.UNCHANGED == "unchanged"


class TestPageChange:
    def test_creation(self):
        now = datetime.utcnow()
        change = PageChange(
            url="https://example.com/page",
            change_type=ChangeType.MODIFIED,
            old_hash="abc123",
            new_hash="def456",
            diff="@@ -1,3 +1,4 @@",
            detected_at=now,
        )
        assert change.url == "https://example.com/page"
        assert change.change_type == ChangeType.MODIFIED
        assert change.old_hash == "abc123"
        assert change.new_hash == "def456"
        assert change.diff == "@@ -1,3 +1,4 @@"

    def test_minimal(self):
        change = PageChange(url="https://example.com", change_type=ChangeType.ADDED)
        assert change.url == "https://example.com"
        assert change.change_type == ChangeType.ADDED
        assert change.old_hash is None
        assert change.new_hash is None
        assert change.diff is None
        assert change.detected_at is not None

    def test_serialization_roundtrip(self):
        change = PageChange(
            url="https://example.com/page",
            change_type=ChangeType.ADDED,
            new_hash="newhash",
        )
        data = change.model_dump()
        restored = PageChange(**data)
        assert restored.url == change.url
        assert restored.change_type == change.change_type
        assert restored.new_hash == change.new_hash


class TestChangeReport:
    def test_creation(self):
        report = ChangeReport(skill_name="test-skill", total_pages=10)
        assert report.skill_name == "test-skill"
        assert report.total_pages == 10
        assert report.added == []
        assert report.modified == []
        assert report.deleted == []
        assert report.unchanged == 0

    def test_has_changes_true(self):
        report = ChangeReport(
            skill_name="test-skill",
            total_pages=10,
            modified=[
                PageChange(
                    url="https://example.com",
                    change_type=ChangeType.MODIFIED,
                    old_hash="a",
                    new_hash="b",
                )
            ],
        )
        assert report.has_changes is True

    def test_has_changes_false(self):
        report = ChangeReport(skill_name="test-skill", total_pages=10, unchanged=10)
        assert report.has_changes is False

    def test_change_count(self):
        report = ChangeReport(
            skill_name="test-skill",
            total_pages=10,
            added=[PageChange(url="https://a.com", change_type=ChangeType.ADDED)],
            modified=[
                PageChange(
                    url="https://b.com", change_type=ChangeType.MODIFIED, old_hash="a", new_hash="b"
                )
            ],
            deleted=[PageChange(url="https://c.com", change_type=ChangeType.DELETED)],
        )
        assert report.change_count == 3

    def test_change_count_zero(self):
        report = ChangeReport(skill_name="test-skill", total_pages=5, unchanged=5)
        assert report.change_count == 0


class TestSyncConfig:
    def test_defaults(self):
        config = SyncConfig(skill_config="configs/test.json")
        assert config.skill_config == "configs/test.json"
        assert config.check_interval == 3600
        assert config.enabled is True
        assert config.auto_update is False
        assert config.notify_on_change is True
        assert config.notification_channels == []
        assert config.webhook_url is None
        assert config.email_recipients == []
        assert config.slack_webhook is None

    def test_full_config(self):
        config = SyncConfig(
            skill_config="configs/react.json",
            check_interval=1800,
            auto_update=True,
            notification_channels=["slack", "webhook"],
            webhook_url="https://hooks.example.com/webhook",
            slack_webhook="https://hooks.slack.com/services/T000/B000/XXX",
            email_recipients=["dev@example.com"],
        )
        assert config.check_interval == 1800
        assert config.auto_update is True
        assert "slack" in config.notification_channels
        assert config.webhook_url == "https://hooks.example.com/webhook"
        assert "dev@example.com" in config.email_recipients

    def test_serialization_roundtrip(self):
        config = SyncConfig(
            skill_config="configs/test.json",
            notification_channels=["slack", "email"],
            email_recipients=["a@b.com", "c@d.com"],
        )
        data = config.model_dump()
        restored = SyncConfig(**data)
        assert restored.skill_config == config.skill_config
        assert restored.notification_channels == ["slack", "email"]
        assert len(restored.email_recipients) == 2


class TestSyncState:
    def test_defaults(self):
        state = SyncState(skill_name="test-skill")
        assert state.skill_name == "test-skill"
        assert state.last_check is None
        assert state.last_change is None
        assert state.total_checks == 0
        assert state.total_changes == 0
        assert state.page_hashes == {}
        assert state.status == "idle"
        assert state.error is None

    def test_active_state(self):
        now = datetime.utcnow()
        state = SyncState(
            skill_name="test-skill",
            last_check=now,
            total_checks=5,
            total_changes=2,
            page_hashes={"https://a.com": "abc123"},
            status="checking",
        )
        assert state.total_checks == 5
        assert state.total_changes == 2
        assert state.status == "checking"
        assert len(state.page_hashes) == 1

    def test_error_state(self):
        state = SyncState(skill_name="test-skill", status="error", error="Connection refused")
        assert state.status == "error"
        assert state.error == "Connection refused"


class TestWebhookPayload:
    def test_creation(self):
        payload = WebhookPayload(
            event="change_detected",
            skill_name="test-skill",
            metadata={"source": "periodic_check"},
        )
        assert payload.event == "change_detected"
        assert payload.skill_name == "test-skill"
        assert payload.metadata == {"source": "periodic_check"}
        assert payload.timestamp is not None
        assert payload.changes is None

    def test_with_changes(self):
        report = ChangeReport(
            skill_name="test-skill",
            total_pages=10,
            modified=[
                PageChange(
                    url="https://a.com", change_type=ChangeType.MODIFIED, old_hash="a", new_hash="b"
                )
            ],
        )
        payload = WebhookPayload(event="sync_complete", skill_name="test-skill", changes=report)
        assert payload.changes == report
        assert payload.changes.has_changes is True
