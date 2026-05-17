"""Use case: mark a single notification as read."""

from __future__ import annotations

import uuid

from apps.notifications.domain.entities import NotificationEntity
from apps.notifications.domain.repositories import INotificationRepository


class MarkNotificationReadUseCase:
    """Mark a notification as read; idempotent if already read."""

    def __init__(self, notif_repo: INotificationRepository) -> None:
        self._notifs = notif_repo

    def execute(self, *, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """
        Set is_read=True and read_at=now on the notification.

        @param notification_id - the notification to mark
        @param user_id - must own the notification
        @returns the updated NotificationEntity
        @raises NotificationNotFoundError if not found or not owned
        """
        notification = self._notifs.get_by_id(notification_id, user_id)
        if notification.is_read:
            return notification
        return self._notifs.mark_read(notification_id, user_id)
