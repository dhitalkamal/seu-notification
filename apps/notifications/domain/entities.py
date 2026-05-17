"""Pure Python domain entities for the notifications module with no framework dependencies."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class EmailNotification:
    """Represents a single outbound email to be delivered."""

    to_email: str
    to_name: str
    subject: str
    html_body: str


@dataclass(slots=True)
class NotificationEntity:
    """A single notification record for a platform user."""

    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    channel: str
    title: str
    message: str
    status: str
    is_read: bool
    created_at: datetime
    data: dict = field(default_factory=dict)
    read_at: datetime | None = None


@dataclass(slots=True)
class NotificationPreferenceEntity:
    """Per-user, per-type channel preferences. Defaults to email/push/in_app ON, sms OFF."""

    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
