"""Use case: upsert notification channel preferences for a user."""

from __future__ import annotations

import uuid

from apps.notifications.domain.entities import NotificationPreferenceEntity
from apps.notifications.domain.repositories import INotificationPreferenceRepository


class UpdateNotificationPreferenceUseCase:
    """Create or overwrite a user's channel preferences for a notification type."""

    def __init__(self, preference_repo: INotificationPreferenceRepository) -> None:
        self._preferences = preference_repo

    def execute(
        self,
        *,
        user_id: uuid.UUID,
        notification_type: str,
        email_enabled: bool,
        push_enabled: bool,
        sms_enabled: bool,
        in_app_enabled: bool,
    ) -> NotificationPreferenceEntity:
        """
        Upsert preferences for (user_id, notification_type).

        @param user_id - the user whose preferences to update
        @param notification_type - e.g. general, event_reminder
        """
        entity = NotificationPreferenceEntity(
            id=uuid.uuid4(),
            user_id=user_id,
            notification_type=notification_type,
            email_enabled=email_enabled,
            push_enabled=push_enabled,
            sms_enabled=sms_enabled,
            in_app_enabled=in_app_enabled,
        )
        return self._preferences.upsert(entity)
