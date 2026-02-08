"""
Pydantic models for sync system.
"""

from typing import Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Type of change detected."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


class PageChange(BaseModel):
    """Represents a change to a single page."""

    url: str = Field(..., description="Page URL")
    change_type: ChangeType = Field(..., description="Type of change")
    old_hash: str | None = Field(None, description="Previous content hash")
    new_hash: str | None = Field(None, description="New content hash")
    diff: str | None = Field(None, description="Content diff (if available)")
    detected_at: datetime = Field(
        default_factory=datetime.utcnow, description="When change was detected"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://react.dev/learn/thinking-in-react",
                "change_type": "modified",
                "old_hash": "abc123",
                "new_hash": "def456",
                "diff": "@@ -10,3 +10,4 @@\n+New content here",
                "detected_at": "2024-01-15T10:30:00Z",
            }
        }


class ChangeReport(BaseModel):
    """Report of all changes detected."""

    skill_name: str = Field(..., description="Skill name")
    total_pages: int = Field(..., description="Total pages checked")
    added: list[PageChange] = Field(default_factory=list, description="Added pages")
    modified: list[PageChange] = Field(default_factory=list, description="Modified pages")
    deleted: list[PageChange] = Field(default_factory=list, description="Deleted pages")
    unchanged: int = Field(0, description="Number of unchanged pages")
    checked_at: datetime = Field(
        default_factory=datetime.utcnow, description="When check was performed"
    )

    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return bool(self.added or self.modified or self.deleted)

    @property
    def change_count(self) -> int:
        """Total number of changes."""
        return len(self.added) + len(self.modified) + len(self.deleted)


class SyncConfig(BaseModel):
    """Configuration for sync monitoring."""

    skill_config: str = Field(..., description="Path to skill config file")
    check_interval: int = Field(
        default=3600, description="Check interval in seconds (default: 1 hour)"
    )
    enabled: bool = Field(default=True, description="Whether sync is enabled")
    auto_update: bool = Field(default=False, description="Automatically rebuild skill on changes")
    notify_on_change: bool = Field(default=True, description="Send notifications on changes")
    notification_channels: list[str] = Field(
        default_factory=list, description="Notification channels (email, slack, webhook)"
    )
    webhook_url: str | None = Field(None, description="Webhook URL for change notifications")
    email_recipients: list[str] = Field(
        default_factory=list, description="Email recipients for notifications"
    )
    slack_webhook: str | None = Field(None, description="Slack webhook URL")

    class Config:
        json_schema_extra = {
            "example": {
                "skill_config": "configs/react.json",
                "check_interval": 3600,
                "enabled": True,
                "auto_update": False,
                "notify_on_change": True,
                "notification_channels": ["slack", "webhook"],
                "webhook_url": "https://example.com/webhook",
                "slack_webhook": "https://hooks.slack.com/services/...",
            }
        }


class SyncState(BaseModel):
    """Current state of sync monitoring."""

    skill_name: str = Field(..., description="Skill name")
    last_check: datetime | None = Field(None, description="Last check time")
    last_change: datetime | None = Field(None, description="Last change detected")
    total_checks: int = Field(default=0, description="Total checks performed")
    total_changes: int = Field(default=0, description="Total changes detected")
    page_hashes: dict[str, str] = Field(
        default_factory=dict, description="URL -> content hash mapping"
    )
    status: str = Field(default="idle", description="Current status")
    error: str | None = Field(None, description="Last error message")


class WebhookPayload(BaseModel):
    """Payload for webhook notifications."""

    event: str = Field(..., description="Event type (change_detected, sync_complete)")
    skill_name: str = Field(..., description="Skill name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    changes: ChangeReport | None = Field(None, description="Change report")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "event": "change_detected",
                "skill_name": "react",
                "timestamp": "2024-01-15T10:30:00Z",
                "changes": {
                    "total_pages": 150,
                    "added": [],
                    "modified": [{"url": "https://react.dev/learn"}],
                    "deleted": [],
                },
                "metadata": {"source": "periodic_check"},
            }
        }
