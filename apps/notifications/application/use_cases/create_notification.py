"""Use case: create a notification and deliver it based on channel and preferences."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from apps.notifications.domain.entities import NotificationEntity
from apps.notifications.domain.repositories import (
    INotificationPreferenceRepository,
    INotificationRepository,
    IPublisher,
)


class CreateNotificationUseCase:
    """Create a notification record and trigger delivery for the appropriate channel."""

    def __init__(
        self,
        notif_repo: INotificationRepository,
        pref_repo: INotificationPreferenceRepository,
        publisher: IPublisher,
    ) -> None:
        self._notifs = notif_repo
        self._prefs = pref_repo
        self._publisher = publisher

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
        Check preferences, set status, persist, and publish for email channel.

        @param user_id - the recipient of the notification
        @param notification_type - e.g. registration_confirmed, password_reset
        @param channel - in_app | email | push | sms
        @param title - notification title, used as email subject
        @param message - notification body, used as email content
        @param data - JSONB payload; for email must include to_email and to_name
        @returns the persisted NotificationEntity
        """
        if data is None:
            data = {}

        pref = self._prefs.get_or_default(user_id, notification_type)

        channel_enabled = {
            "in_app": pref.in_app_enabled,
            "email": pref.email_enabled,
            "push": pref.push_enabled,
            "sms": pref.sms_enabled,
        }.get(channel, True)

        if not channel_enabled:
            status = "failed"
        elif channel == "in_app":
            status = "delivered"
        else:
            status = "pending"

        notification = NotificationEntity(
            id=uuid.uuid4(),
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            title=title,
            message=message,
            status=status,
            is_read=False,
            created_at=datetime.now(timezone.utc),
            data=data,
        )
        result = self._notifs.create(notification)

        if status == "pending" and channel == "email":
            html_body = f"<h2>{title}</h2><p>{message}</p>"
            self._publisher.publish(
                notification_id=result.id,
                to_email=data.get("to_email", ""),
                to_name=data.get("to_name", ""),
                subject=title,
                html_body=html_body,
            )

        return result
