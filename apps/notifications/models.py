"""Re-export ORM models so Django's app registry finds them under the notifications label."""

from __future__ import annotations

from apps.notifications.infrastructure.models import (
    DeviceToken,
    Notification,
    NotificationPreference,
)

__all__ = ["DeviceToken", "Notification", "NotificationPreference"]
