"""Re-export ORM models so Django's app registry finds them under the notifications label."""

from __future__ import annotations

from apps.notifications.infrastructure.digest_models import AuditDigestSchedule
from apps.notifications.infrastructure.models import (
    DeviceToken,
    EventJourney,
    JourneyStage,
    Notification,
    NotificationPreference,
)

__all__ = [
    "AuditDigestSchedule",
    "DeviceToken",
    "EventJourney",
    "JourneyStage",
    "Notification",
    "NotificationPreference",
]
