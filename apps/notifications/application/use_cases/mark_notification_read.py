"""Use case: mark a single notification as read."""

from __future__ import annotations

import uuid

from apps.notifications.domain.entities import NotificationEntity
from apps.notifications.domain.repositories import INotificationRepository


class MarkNotificationReadUseCase:
    """Mark a notification as read, enforcing ownership."""

    def __init__(self, notification_repo: INotificationRepository) -> None:
        self._notifications = notification_repo

    def execute(self, *, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """
        Set is_read=True and read_at=now. No-op if already read.

        @raises NotificationNotFoundError if absent or not owned by user
        """
        return self._notifications.mark_read(notification_id, user_id)
