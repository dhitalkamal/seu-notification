"""Concrete repository implementations backed by the Django ORM."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from apps.notifications.domain.entities import NotificationEntity, NotificationPreferenceEntity
from apps.notifications.domain.exceptions import NotificationNotFoundError
from apps.notifications.domain.repositories import (
    INotificationPreferenceRepository,
    INotificationRepository,
)
from apps.notifications.infrastructure.models import Notification, NotificationPreference


class DjangoNotificationRepository(INotificationRepository):
    """Persists Notification entities using the Django ORM."""

    def create(self, entity: NotificationEntity) -> NotificationEntity:
        """Persist a new notification and return the saved entity."""
        obj = Notification.from_entity(entity)
        obj.save(using="default")
        return obj.to_entity()

    def get_by_id(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """Fetch by id and user. Raises NotificationNotFoundError if absent or not owned."""
        try:
            return Notification.objects.get(id=notification_id, user_id=user_id).to_entity()
        except Notification.DoesNotExist:
            raise NotificationNotFoundError("Notification not found.")

    def list_by_user(self, user_id: uuid.UUID) -> list[NotificationEntity]:
        """Return all notifications for this user ordered newest first."""
        return [
            obj.to_entity()
            for obj in Notification.objects.filter(user_id=user_id).order_by("-created_at")
        ]

    def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """Set is_read=True and read_at=now for an unread notification."""
        now = datetime.now(timezone.utc)
        Notification.objects.filter(id=notification_id, user_id=user_id, is_read=False).update(
            is_read=True, read_at=now
        )
        return Notification.objects.get(id=notification_id).to_entity()

    def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Bulk-mark all unread notifications for this user. Returns count."""
        now = datetime.now(timezone.utc)
        return Notification.objects.filter(user_id=user_id, is_read=False).update(
            is_read=True, read_at=now
        )

    def update_status(self, notification_id: uuid.UUID, status: str) -> None:
        """Update a notification status by id (called by consumer after delivery)."""
        Notification.objects.filter(id=notification_id).update(status=status)


class DjangoNotificationPreferenceRepository(INotificationPreferenceRepository):
    """Returns saved notification preferences or in-memory defaults."""

    def get_or_default(
        self, user_id: uuid.UUID, notification_type: str
    ) -> NotificationPreferenceEntity:
        """Return saved preference or an entity with all-default channel settings."""
        try:
            return NotificationPreference.objects.get(
                user_id=user_id, notification_type=notification_type
            ).to_entity()
        except NotificationPreference.DoesNotExist:
            return NotificationPreferenceEntity(
                id=uuid.uuid4(),
                user_id=user_id,
                notification_type=notification_type,
            )
