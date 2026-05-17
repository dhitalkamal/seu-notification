"""Hand-rolled fakes for notification interfaces."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from apps.notifications.domain.entities import (
    EmailNotification,
    NotificationEntity,
    NotificationPreferenceEntity,
)
from apps.notifications.domain.exceptions import EmailDeliveryError, NotificationNotFoundError
from apps.notifications.domain.repositories import (
    IEmailSender,
    INotificationPreferenceRepository,
    INotificationRepository,
    IPublisher,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def make_notification(**kwargs: object) -> NotificationEntity:
    """Build a NotificationEntity with sensible defaults for testing."""
    defaults: dict = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "notification_type": "registration_confirmed",
        "channel": "in_app",
        "title": "Test Notification",
        "message": "This is a test.",
        "status": "delivered",
        "is_read": False,
        "created_at": _now(),
        "data": {},
        "read_at": None,
    }
    defaults.update(kwargs)
    return NotificationEntity(**defaults)  # type: ignore[arg-type]


def make_preference(**kwargs: object) -> NotificationPreferenceEntity:
    """Build a NotificationPreferenceEntity with default channel settings."""
    defaults: dict = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "notification_type": "registration_confirmed",
        "email_enabled": True,
        "push_enabled": True,
        "sms_enabled": False,
        "in_app_enabled": True,
    }
    defaults.update(kwargs)
    return NotificationPreferenceEntity(**defaults)  # type: ignore[arg-type]


class FakeEmailSender(IEmailSender):
    """Records sent notifications. Always succeeds."""

    def __init__(self) -> None:
        self.sent: list[EmailNotification] = []

    def send(self, notification: EmailNotification) -> None:
        """Append to sent list."""
        self.sent.append(notification)


class AlwaysFailEmailSender(IEmailSender):
    """Always raises EmailDeliveryError -- simulates a completely broken transport."""

    def send(self, notification: EmailNotification) -> None:
        """Raise unconditionally."""
        raise EmailDeliveryError("Simulated send failure.")


class FakeNotificationRepository(INotificationRepository):
    """In-memory notification store."""

    def __init__(self, notifications: Sequence[NotificationEntity] | None = None) -> None:
        self._store: dict[uuid.UUID, NotificationEntity] = {n.id: n for n in (notifications or [])}

    def create(self, entity: NotificationEntity) -> NotificationEntity:
        """Persist and return the entity."""
        self._store[entity.id] = entity
        return entity

    def get_by_id(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """Raise NotificationNotFoundError if absent or not owned by user."""
        entity = self._store.get(notification_id)
        if entity is None or entity.user_id != user_id:
            raise NotificationNotFoundError("Notification not found.")
        return entity

    def list_by_user(self, user_id: uuid.UUID) -> list[NotificationEntity]:
        """Return all notifications for this user ordered by created_at descending."""
        return sorted(
            [n for n in self._store.values() if n.user_id == user_id],
            key=lambda n: n.created_at,
            reverse=True,
        )

    def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """Set is_read=True and read_at=now if not already read."""
        entity = self._store[notification_id]
        if not entity.is_read:
            entity.is_read = True
            entity.read_at = _now()
        return entity

    def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications for this user as read. Returns count."""
        count = 0
        for entity in self._store.values():
            if entity.user_id == user_id and not entity.is_read:
                entity.is_read = True
                entity.read_at = _now()
                count += 1
        return count

    def update_status(self, notification_id: uuid.UUID, status: str) -> None:
        """Update the status of a notification by id."""
        if notification_id in self._store:
            self._store[notification_id].status = status


class FakePreferenceRepository(INotificationPreferenceRepository):
    """Returns a configured preference or one with all defaults enabled."""

    def __init__(self, pref: NotificationPreferenceEntity | None = None) -> None:
        self._pref = pref

    def get_or_default(
        self, user_id: uuid.UUID, notification_type: str
    ) -> NotificationPreferenceEntity:
        """Return the configured pref or a default with email/push/in_app ON, sms OFF."""
        if self._pref is not None:
            return self._pref
        return NotificationPreferenceEntity(
            id=uuid.uuid4(),
            user_id=user_id,
            notification_type=notification_type,
        )


class FakePublisher(IPublisher):
    """Records publish calls for assertion in tests."""

    def __init__(self) -> None:
        self.published: list[dict] = []

    def publish(
        self,
        *,
        notification_id: uuid.UUID,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
    ) -> None:
        """Record the call."""
        self.published.append(
            {
                "notification_id": notification_id,
                "to_email": to_email,
                "to_name": to_name,
                "subject": subject,
                "html_body": html_body,
            }
        )
