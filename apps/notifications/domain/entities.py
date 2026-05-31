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
    """A single in-app or channel notification sent to a user."""

    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    channel: str
    title: str
    message: str
    status: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None
    data: dict = field(default_factory=dict)


@dataclass(slots=True)
class NotificationPreferenceEntity:
    """Per-user per-notification-type channel preferences."""

    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True


@dataclass(slots=True)
class DeviceTokenEntity:
    """A push notification device token registered by a user."""

    id: uuid.UUID
    user_id: uuid.UUID
    token: str
    platform: str
    is_active: bool
    created_at: datetime


@dataclass(slots=True)
class JourneyStageEntity:
    """A single timed stage in an event's automated notification journey."""

    id: uuid.UUID
    event_id: uuid.UUID
    stage_type: str
    trigger_at: datetime
    status: str
    created_at: datetime
    fired_at: datetime | None = None


@dataclass(slots=True)
class EventJourneyEntity:
    """The full automated notification journey for one event."""

    id: uuid.UUID
    event_id: uuid.UUID
    event_start: datetime
    event_end: datetime
    created_at: datetime
    stages: list = field(default_factory=list)
