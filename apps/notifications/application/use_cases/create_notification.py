"""Use case: create a notification, respecting user channel preferences."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from apps.notifications.domain.entities import NotificationEntity
from apps.notifications.domain.repositories import (
    INotificationPreferenceRepository,
    INotificationRepository,
)

_CHANNEL_FIELD = {
    "in_app": "in_app_enabled",
    "email": "email_enabled",
    "push": "push_enabled",
    "sms": "sms_enabled",
}


class CreateNotificationUseCase:
    """Persist a notification, setting status based on channel preference."""

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
        user_id: uuid.UUID,
        notification_type: str,
        channel: str,
        title: str,
        message: str,
        data: dict | None = None,
    ) -> NotificationEntity:
        """
        Create a notification. Status is delivered for in_app, pending for other channels.
        If the user has disabled this channel, status is set to failed.

        @param user_id - recipient
        @param notification_type - semantic type e.g. registration_confirmed
        @param channel - in_app | email | push | sms
        @param title - short heading
        @param message - full notification body
        @param data - optional arbitrary payload dict
        """
        pref = self._preferences.get_or_create(user_id, notification_type)
        channel_enabled = getattr(pref, _CHANNEL_FIELD.get(channel, "in_app_enabled"), True)

        if channel_enabled:
            status = "delivered" if channel == "in_app" else "pending"
        else:
            status = "failed"

        entity = NotificationEntity(
            id=uuid.uuid4(),
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            title=title,
            message=message,
            status=status,
            is_read=False,
            created_at=datetime.now(timezone.utc),
            data=data or {},
        )
        return self._notifications.create(entity)
