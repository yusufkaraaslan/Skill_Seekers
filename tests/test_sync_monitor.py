"""Tests for sync monitor (monitor.py)."""

import json
import pytest
from unittest.mock import patch
from skill_seekers.sync.monitor import SyncMonitor
from skill_seekers.sync.models import ChangeReport, ChangeType, PageChange, SyncState


@pytest.fixture
def sample_config(tmp_path):
    config = {"name": "test-skill", "base_url": "https://example.com/docs"}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    return config_path, tmp_path


@pytest.fixture
def monitor(sample_config):
    config_path, tmp_path = sample_config
    state_file = tmp_path / "test-skill_sync.json"
    with (
        patch.object(SyncMonitor, "_save_state"),
        patch.object(SyncMonitor, "_load_state", return_value=SyncState(skill_name="test-skill")),
    ):
        m = SyncMonitor(
            config_path=str(config_path),
            check_interval=60,
            state_file=str(state_file),
        )
        return m


class TestMonitorInit:
    def test_basic_init(self, sample_config):
        config_path, _ = sample_config
        with (
            patch.object(SyncMonitor, "_save_state"),
            patch.object(
                SyncMonitor, "_load_state", return_value=SyncState(skill_name="test-skill")
            ),
        ):
            m = SyncMonitor(config_path=str(config_path))
            assert m.skill_name == "test-skill"
            assert m.check_interval == 3600
            assert m.auto_update is False
            assert m._running is False

    def test_custom_interval(self, sample_config):
        config_path, _ = sample_config
        with (
            patch.object(SyncMonitor, "_save_state"),
            patch.object(
                SyncMonitor, "_load_state", return_value=SyncState(skill_name="test-skill")
            ),
        ):
            m = SyncMonitor(config_path=str(config_path), check_interval=1800)
            assert m.check_interval == 1800

    def test_auto_update(self, sample_config):
        config_path, _ = sample_config
        with (
            patch.object(SyncMonitor, "_save_state"),
            patch.object(
                SyncMonitor, "_load_state", return_value=SyncState(skill_name="test-skill")
            ),
        ):
            m = SyncMonitor(config_path=str(config_path), auto_update=True)
            assert m.auto_update is True

    def test_on_change_callback(self, sample_config):
        config_path, _ = sample_config
        called = []

        def cb(report):
            called.append(report)

        with (
            patch.object(SyncMonitor, "_save_state"),
            patch.object(
                SyncMonitor, "_load_state", return_value=SyncState(skill_name="test-skill")
            ),
        ):
            m = SyncMonitor(config_path=str(config_path), on_change=cb)
            assert m.on_change is cb


class TestCheckNow:
    def test_check_now_no_urls(self, monitor):
        report = monitor.check_now()
        assert isinstance(report, ChangeReport)
        assert report.skill_name == "test-skill"

    def test_check_now_updates_state(self, monitor):
        monitor.check_now()
        assert monitor.state.last_check is not None
        assert monitor.state.total_checks == 1
        assert monitor.state.status == "idle"

    def test_check_now_with_changes(self, sample_config):
        config_path, tmp_path = sample_config
        old_hash = "abc123"
        with (
            patch.object(SyncMonitor, "_save_state"),
        ):
            m = SyncMonitor(
                config_path=str(config_path),
                state_file=str(tmp_path / "state.json"),
            )

            m.state.page_hashes = {"https://example.com/docs": old_hash}

            with patch.object(
                m.detector,
                "check_pages",
                return_value=ChangeReport(
                    skill_name="test-skill",
                    total_pages=1,
                    modified=[
                        PageChange(
                            url="https://example.com/docs",
                            change_type=ChangeType.MODIFIED,
                            old_hash=old_hash,
                            new_hash="newhash",
                        )
                    ],
                ),
            ):
                m.check_now()
                assert m.state.total_changes == 1
                assert "https://example.com/docs" in m.state.page_hashes

    def test_callback_triggered_on_changes(self, sample_config):
        config_path, tmp_path = sample_config
        called = []

        def cb(report):
            called.append(report)

        mock_change = ChangeReport(
            skill_name="test-skill",
            total_pages=1,
            modified=[
                PageChange(
                    url="https://example.com/docs",
                    change_type=ChangeType.MODIFIED,
                    old_hash="a",
                    new_hash="b",
                )
            ],
        )

        with (
            patch.object(SyncMonitor, "_save_state"),
            patch.object(SyncMonitor, "_notify"),
        ):
            m = SyncMonitor(
                config_path=str(config_path),
                state_file=str(tmp_path / "state.json"),
                on_change=cb,
            )

            with patch.object(m.detector, "check_pages", return_value=mock_change):
                m.check_now()
                assert len(called) == 1
                assert called[0] is mock_change


class TestStatePersistence:
    def test_load_state_new(self, sample_config):
        config_path, tmp_path = sample_config
        with patch.object(SyncMonitor, "_save_state"):
            m = SyncMonitor(
                config_path=str(config_path),
                state_file=str(tmp_path / "state.json"),
            )
            state = m._load_state()
            assert state.skill_name == "test-skill"
            assert state.total_checks == 0

    def test_save_and_load_state(self, sample_config):
        config_path, tmp_path = sample_config
        state_file = tmp_path / "state.json"

        m = SyncMonitor(
            config_path=str(config_path),
            state_file=str(state_file),
        )
        m.state.total_checks = 5
        m.state.page_hashes = {"https://a.com": "abc"}

        m._save_state()

        assert state_file.exists()

        loaded_data = json.loads(state_file.read_text())
        assert loaded_data["total_checks"] == 5
        assert loaded_data["page_hashes"]["https://a.com"] == "abc"


class TestStats:
    def test_stats(self, monitor):
        monitor.state.total_checks = 10
        monitor.state.total_changes = 3
        monitor.state.page_hashes = {"https://a.com": "abc", "https://b.com": "def"}
        monitor.state.status = "idle"

        stats = monitor.stats()

        assert stats["skill_name"] == "test-skill"
        assert stats["total_checks"] == 10
        assert stats["total_changes"] == 3
        assert stats["tracked_pages"] == 2
        assert stats["status"] == "idle"
        assert stats["running"] is False


class TestContextManager:
    def test_context_manager(self, sample_config):
        config_path, _ = sample_config
        with (
            patch.object(SyncMonitor, "_save_state"),
            patch.object(
                SyncMonitor, "_load_state", return_value=SyncState(skill_name="test-skill")
            ),
            patch.object(SyncMonitor, "check_now"),
        ):
            m = SyncMonitor(config_path=str(config_path), check_interval=86400)
            m._thread = None

            with patch.object(m, "start") as mock_start, patch.object(m, "stop") as mock_stop:
                with m as mon:
                    assert mon is m
                    mock_start.assert_called_once()
                mock_stop.assert_called_once()


class TestErrorHandling:
    def test_check_now_records_error(self, sample_config):
        config_path, tmp_path = sample_config
        with (
            patch.object(SyncMonitor, "_save_state"),
        ):
            m = SyncMonitor(
                config_path=str(config_path),
                state_file=str(tmp_path / "state.json"),
            )

            with patch.object(m.detector, "check_pages", side_effect=RuntimeError("Test error")):  # noqa: SIM117
                with pytest.raises(RuntimeError, match="Test error"):
                    m.check_now()

            assert m.state.status == "error"
            assert m.state.error == "Test error"
