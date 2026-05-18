"""Concrete repository implementations backed by the Django ORM."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from apps.notifications.domain.entities import (
    DeviceTokenEntity,
    NotificationEntity,
    NotificationPreferenceEntity,
)
from apps.notifications.domain.exceptions import NotificationNotFoundError
from apps.notifications.domain.repositories import (
    IDeviceTokenRepository,
    INotificationPreferenceRepository,
    INotificationRepository,
)
from apps.notifications.infrastructure.models import (
    DeviceToken,
    Notification,
    NotificationPreference,
)


class DjangoNotificationRepository(INotificationRepository):
    """Persists Notification entities using the Django ORM."""

    def create(self, entity: NotificationEntity) -> NotificationEntity:
        """Persist a new notification and return the saved entity."""
        obj = Notification.from_entity(entity)
        obj.save()
        return obj.to_entity()

    def get_by_id(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """Fetch by id enforcing ownership. Raises NotificationNotFoundError if absent."""
        try:
            return Notification.objects.get(id=notification_id, user_id=user_id).to_entity()
        except Notification.DoesNotExist:
            raise NotificationNotFoundError("Notification not found.")

    def list_by_user(self, user_id: uuid.UUID) -> list[NotificationEntity]:
        """Return all notifications for this user, newest first."""
        return [
            obj.to_entity()
            for obj in Notification.objects.filter(user_id=user_id).order_by("-created_at")
        ]

    def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """Set is_read=True and read_at=now. No-op if already read."""
        try:
            obj = Notification.objects.get(id=notification_id, user_id=user_id)
        except Notification.DoesNotExist:
            raise NotificationNotFoundError("Notification not found.")
        if not obj.is_read:
            obj.is_read = True
            obj.read_at = datetime.now(timezone.utc)
            obj.save(update_fields=["is_read", "read_at"])
        return obj.to_entity()

    def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications for this user as read. Returns count updated."""
        now = datetime.now(timezone.utc)
        updated, _ = Notification.objects.filter(user_id=user_id, is_read=False).update(
            is_read=True, read_at=now
        )
        return updated

    def unread_count(self, user_id: uuid.UUID) -> int:
        """Return the number of unread notifications for this user."""
        return Notification.objects.filter(user_id=user_id, is_read=False).count()


class DjangoNotificationPreferenceRepository(INotificationPreferenceRepository):
    """Persists NotificationPreference entities using the Django ORM."""

    def get_or_create(
        self, user_id: uuid.UUID, notification_type: str
    ) -> NotificationPreferenceEntity:
        """Return existing preference or create a default one."""
        obj, _ = NotificationPreference.objects.get_or_create(
            user_id=user_id,
            notification_type=notification_type,
            defaults={"id": uuid.uuid4()},
        )
        return obj.to_entity()

    def upsert(self, entity: NotificationPreferenceEntity) -> NotificationPreferenceEntity:
        """Insert or update the preference for (user_id, notification_type)."""
        obj, _ = NotificationPreference.objects.update_or_create(
            user_id=entity.user_id,
            notification_type=entity.notification_type,
            defaults={
                "id": entity.id,
                "email_enabled": entity.email_enabled,
                "push_enabled": entity.push_enabled,
                "sms_enabled": entity.sms_enabled,
                "in_app_enabled": entity.in_app_enabled,
            },
        )
        return obj.to_entity()


class DjangoDeviceTokenRepository(IDeviceTokenRepository):
    """Persists DeviceToken entities using the Django ORM."""

    def register(self, entity: DeviceTokenEntity) -> DeviceTokenEntity:
        """Insert or reactivate an existing device token."""
        obj, _ = DeviceToken.objects.update_or_create(
            token=entity.token,
            defaults={
                "id": entity.id,
                "user_id": entity.user_id,
                "platform": entity.platform,
                "is_active": True,
            },
        )
        return obj.to_entity()

    def list_by_user(self, user_id: uuid.UUID) -> list[DeviceTokenEntity]:
        """Return all active device tokens for a user."""
        return [t.to_entity() for t in DeviceToken.objects.filter(user_id=user_id, is_active=True)]
