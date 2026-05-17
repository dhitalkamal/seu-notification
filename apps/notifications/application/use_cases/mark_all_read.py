"""Use case: mark all of a user's unread notifications as read."""

from __future__ import annotations

import uuid

from apps.notifications.domain.repositories import INotificationRepository


class MarkAllReadUseCase:
    """Bulk-mark every unread notification for a user as read."""

    def __init__(self, notification_repo: INotificationRepository) -> None:
        self._notifications = notification_repo

    def execute(self, *, user_id: uuid.UUID) -> int:
        """
        Mark all unread notifications for user_id as read.

        @returns count of notifications updated
        """
        return self._notifications.mark_all_read(user_id)
