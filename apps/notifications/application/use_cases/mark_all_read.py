"""Use case: mark all of a user's unread notifications as read."""

from __future__ import annotations

import uuid

from apps.notifications.domain.repositories import INotificationRepository


class MarkAllReadUseCase:
    """Bulk-mark all unread notifications for a user and return the count."""

    def __init__(self, notif_repo: INotificationRepository) -> None:
        self._notifs = notif_repo

    def execute(self, *, user_id: uuid.UUID) -> int:
        """Return the number of notifications that were just marked as read."""
        return self._notifs.mark_all_read(user_id)
