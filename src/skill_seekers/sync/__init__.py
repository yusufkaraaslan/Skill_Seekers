"""
Real-time documentation sync system.

Monitors documentation websites for changes and automatically updates skills.

Features:
- Change detection (content hashing, last-modified headers)
- Incremental updates (only fetch changed pages)
- Webhook support (push-based notifications)
- Scheduling (periodic checks with cron-like syntax)
- Diff generation (see what changed)
- Notifications (email, Slack, webhook)

Usage:
    # Create sync monitor
    from skill_seekers.sync import SyncMonitor

    monitor = SyncMonitor(
        config_path="configs/react.json",
        check_interval=3600  # 1 hour
    )

    # Start monitoring
    monitor.start()

    # Or run once
    changes = monitor.check_for_updates()
"""

from .monitor import SyncMonitor
from .detector import ChangeDetector
from .models import SyncConfig, ChangeReport, PageChange

__all__ = [
    "SyncMonitor",
    "ChangeDetector",
    "SyncConfig",
    "ChangeReport",
    "PageChange",
]
