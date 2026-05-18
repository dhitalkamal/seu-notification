"""Use case: create notifications for up to 1,000 users in one batch."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from apps.notifications.domain.entities import NotificationEntity
from apps.notifications.domain.repositories import (
    INotificationPreferenceRepository,
    INotificationRepository,
)

_BATCH_LIMIT = 1000

_CHANNEL_FIELD = {
    "in_app": "in_app_enabled",
    "email": "email_enabled",
    "push": "push_enabled",
    "sms": "sms_enabled",
}


class BatchCreateNotificationsUseCase:
    """Send the same notification to many users, skipping those who opted out."""

    def __init__(
        self,
        notification_repo: INotificationRepository,
        preference_repo: INotificationPreferenceRepository,
    ) -> None:
        self._notifications = notification_repo
        self._preferences = preference_repo

    def execute(
        self,
        *,
        user_ids: list[uuid.UUID],
        notification_type: str,
        channel: str,
        title: str,
        message: str,
        data: dict | None = None,
    ) -> list[NotificationEntity]:
        """
        Build and bulk-insert notifications for the first 1,000 user_ids.

        Users who disabled the given channel are silently skipped.
        Returns only the notifications that were actually created.
        """
        now = datetime.now(timezone.utc)
        channel_attr = _CHANNEL_FIELD.get(channel, "in_app_enabled")
        to_create: list[NotificationEntity] = []

        for user_id in user_ids[:_BATCH_LIMIT]:
            pref = self._preferences.get_or_create(user_id, notification_type)
            if not getattr(pref, channel_attr, True):
                continue
            status = "delivered" if channel == "in_app" else "pending"
            to_create.append(
                NotificationEntity(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    notification_type=notification_type,
                    channel=channel,
                    title=title,
                    message=message,
                    status=status,
                    is_read=False,
                    created_at=now,
                    data=data or {},
                )
            )

        if not to_create:
            return []
        return self._notifications.batch_create(to_create)
