"""
Sync monitor for continuous documentation monitoring.
"""

import json
import time
import threading
from pathlib import Path
from collections.abc import Callable
from datetime import datetime
import schedule

from .detector import ChangeDetector
from .models import SyncState, ChangeReport, WebhookPayload
from .notifier import Notifier


class SyncMonitor:
    """
    Monitors documentation for changes and triggers updates.

    Features:
    - Continuous monitoring with configurable intervals
    - State persistence (resume after restart)
    - Change detection and diff generation
    - Notification system
    - Auto-update capability

    Examples:
        # Basic usage
        monitor = SyncMonitor(
            config_path="configs/react.json",
            check_interval=3600
        )
        monitor.start()

        # With auto-update
        monitor = SyncMonitor(
            config_path="configs/react.json",
            auto_update=True,
            on_change=lambda report: print(f"Detected {report.change_count} changes")
        )

        # Run once
        changes = monitor.check_now()
    """

    def __init__(
        self,
        config_path: str,
        check_interval: int = 3600,
        auto_update: bool = False,
        state_file: str | None = None,
        on_change: Callable[[ChangeReport], None] | None = None,
    ):
        """
        Initialize sync monitor.

        Args:
            config_path: Path to skill config file
            check_interval: Check interval in seconds
            auto_update: Auto-rebuild skill on changes
            state_file: Path to state file (default: {skill_name}_sync.json)
            on_change: Callback function for change events
        """
        self.config_path = Path(config_path)
        self.check_interval = check_interval
        self.auto_update = auto_update
        self.on_change = on_change

        # Load skill config
        with open(self.config_path) as f:
            self.skill_config = json.load(f)

        self.skill_name = self.skill_config.get("name", "unknown")

        # State file
        if state_file:
            self.state_file = Path(state_file)
        else:
            self.state_file = Path(f"{self.skill_name}_sync.json")

        # Initialize components
        self.detector = ChangeDetector()
        self.notifier = Notifier()

        # Load state
        self.state = self._load_state()

        # Threading
        self._running = False
        self._thread = None

    def _load_state(self) -> SyncState:
        """Load state from file or create new."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                data = json.load(f)
                # Convert datetime strings back
                if data.get("last_check"):
                    data["last_check"] = datetime.fromisoformat(data["last_check"])
                if data.get("last_change"):
                    data["last_change"] = datetime.fromisoformat(data["last_change"])
                return SyncState(**data)
        else:
            return SyncState(skill_name=self.skill_name)

    def _save_state(self):
        """Save current state to file."""
        # Convert datetime to ISO format
        data = self.state.dict()
        if data.get("last_check"):
            data["last_check"] = data["last_check"].isoformat()
        if data.get("last_change"):
            data["last_change"] = data["last_change"].isoformat()

        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    def check_now(self, generate_diffs: bool = False) -> ChangeReport:
        """
        Check for changes now (synchronous).

        Args:
            generate_diffs: Whether to generate content diffs

        Returns:
            ChangeReport with detected changes
        """
        self.state.status = "checking"
        self._save_state()

        try:
            # Get URLs to check from config
            base_url = self.skill_config.get("base_url")
            # TODO: In real implementation, get actual URLs from scraper

            # For now, simulate with base URL only
            urls = [base_url] if base_url else []

            # Check for changes
            report = self.detector.check_pages(
                urls=urls, previous_hashes=self.state.page_hashes, generate_diffs=generate_diffs
            )
            report.skill_name = self.skill_name

            # Update state
            self.state.last_check = datetime.utcnow()
            self.state.total_checks += 1

            if report.has_changes:
                self.state.last_change = datetime.utcnow()
                self.state.total_changes += report.change_count

                # Update hashes for modified pages
                for change in report.added + report.modified:
                    if change.new_hash:
                        self.state.page_hashes[change.url] = change.new_hash

                # Remove deleted pages
                for change in report.deleted:
                    self.state.page_hashes.pop(change.url, None)

                # Trigger callback
                if self.on_change:
                    self.on_change(report)

                # Send notifications
                self._notify(report)

                # Auto-update if enabled
                if self.auto_update:
                    self._trigger_update(report)

            self.state.status = "idle"
            self.state.error = None

            return report

        except Exception as e:
            self.state.status = "error"
            self.state.error = str(e)
            raise
        finally:
            self._save_state()

    def _notify(self, report: ChangeReport):
        """Send notifications about changes."""
        payload = WebhookPayload(
            event="change_detected",
            skill_name=self.skill_name,
            changes=report,
            metadata={"auto_update": self.auto_update},
        )

        self.notifier.send(payload)

    def _trigger_update(self, report: ChangeReport):
        """Trigger skill rebuild."""
        print(f"🔄 Auto-updating {self.skill_name} due to {report.change_count} changes...")
        # TODO: Integrate with doc_scraper to rebuild skill
        # For now, just log
        print(f"  Added: {len(report.added)}")
        print(f"  Modified: {len(report.modified)}")
        print(f"  Deleted: {len(report.deleted)}")

    def start(self):
        """Start continuous monitoring."""
        if self._running:
            raise RuntimeError("Monitor is already running")

        self._running = True

        # Schedule checks
        schedule.every(self.check_interval).seconds.do(lambda: self.check_now())

        # Run in thread
        def run_schedule():
            while self._running:
                schedule.run_pending()
                time.sleep(1)

        self._thread = threading.Thread(target=run_schedule, daemon=True)
        self._thread.start()

        print(f"✅ Started monitoring {self.skill_name} (every {self.check_interval}s)")

        # Run first check immediately
        self.check_now()

    def stop(self):
        """Stop monitoring."""
        if not self._running:
            return

        self._running = False

        if self._thread:
            self._thread.join(timeout=5)

        print(f"🛑 Stopped monitoring {self.skill_name}")

    def stats(self) -> dict:
        """Get monitoring statistics."""
        return {
            "skill_name": self.skill_name,
            "status": self.state.status,
            "last_check": self.state.last_check.isoformat() if self.state.last_check else None,
            "last_change": self.state.last_change.isoformat() if self.state.last_change else None,
            "total_checks": self.state.total_checks,
            "total_changes": self.state.total_changes,
            "tracked_pages": len(self.state.page_hashes),
            "running": self._running,
        }

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
