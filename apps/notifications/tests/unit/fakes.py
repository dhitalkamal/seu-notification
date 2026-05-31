"""Hand-rolled fakes for notification interfaces."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from apps.notifications.domain.entities import (
    DeviceTokenEntity,
    EmailNotification,
    EventJourneyEntity,
    JourneyStageEntity,
    NotificationEntity,
    NotificationPreferenceEntity,
)
from apps.notifications.domain.exceptions import EmailDeliveryError, NotificationNotFoundError
from apps.notifications.domain.repositories import (
    IDeviceTokenRepository,
    IEmailSender,
    IEventJourneyRepository,
    INotificationPreferenceRepository,
    INotificationRepository,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def make_notification(**kwargs: object) -> NotificationEntity:
    """Build a NotificationEntity with sensible defaults."""
    defaults: dict = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "notification_type": "general",
        "channel": "in_app",
        "title": "Test Notification",
        "message": "This is a test.",
        "status": "delivered",
        "is_read": False,
        "created_at": _now(),
        "read_at": None,
        "data": {},
    }
    defaults.update(kwargs)
    return NotificationEntity(**defaults)  # type: ignore[arg-type]


def make_preference(**kwargs: object) -> NotificationPreferenceEntity:
    """Build a NotificationPreferenceEntity with sensible defaults."""
    defaults: dict = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "notification_type": "general",
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
    """Always raises EmailDeliveryError - simulates a completely broken transport."""

    def send(self, notification: EmailNotification) -> None:
        """Raise unconditionally."""
        raise EmailDeliveryError("Simulated send failure.")


class FakeNotificationRepository(INotificationRepository):
    """In-memory notification store."""

    def __init__(self, notifications: list[NotificationEntity] | None = None) -> None:
        self._store: dict[uuid.UUID, NotificationEntity] = {n.id: n for n in (notifications or [])}

    def create(self, entity: NotificationEntity) -> NotificationEntity:
        """Persist and return."""
        self._store[entity.id] = entity
        return entity

    def get_by_id(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """Return notification or raise NotificationNotFoundError."""
        entity = self._store.get(notification_id)
        if entity is None or entity.user_id != user_id:
            raise NotificationNotFoundError("Notification not found.")
        return entity

    def list_by_user(self, user_id: uuid.UUID) -> list[NotificationEntity]:
        """Return all for user."""
        return [n for n in self._store.values() if n.user_id == user_id]

    def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity:
        """Set is_read=True."""
        entity = self.get_by_id(notification_id, user_id)
        if not entity.is_read:
            entity.is_read = True
            entity.read_at = _now()
            self._store[entity.id] = entity
        return entity

    def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread for user. Returns count updated."""
        count = 0
        for entity in list(self._store.values()):
            if entity.user_id == user_id and not entity.is_read:
                entity.is_read = True
                entity.read_at = _now()
                self._store[entity.id] = entity
                count += 1
        return count

    def unread_count(self, user_id: uuid.UUID) -> int:
        """Return count of unread notifications for user."""
        return sum(1 for n in self._store.values() if n.user_id == user_id and not n.is_read)

    def batch_create(self, entities: list[NotificationEntity]) -> list[NotificationEntity]:
        """Persist all entities and return them."""
        for entity in entities:
            self._store[entity.id] = entity
        return entities


class FakeNotificationPreferenceRepository(INotificationPreferenceRepository):
    """In-memory preference store keyed on (user_id, notification_type)."""

    def __init__(self, preferences: list[NotificationPreferenceEntity] | None = None) -> None:
        self._store: dict[tuple, NotificationPreferenceEntity] = {(p.user_id, p.notification_type): p for p in (preferences or [])}

    def get_or_create(self, user_id: uuid.UUID, notification_type: str) -> NotificationPreferenceEntity:
        """Return existing or create default."""
        key = (user_id, notification_type)
        if key not in self._store:
            self._store[key] = NotificationPreferenceEntity(
                id=uuid.uuid4(),
                user_id=user_id,
                notification_type=notification_type,
            )
        return self._store[key]

    def upsert(self, entity: NotificationPreferenceEntity) -> NotificationPreferenceEntity:
        """Insert or update."""
        key = (entity.user_id, entity.notification_type)
        self._store[key] = entity
        return entity


class FakeDeviceTokenRepository(IDeviceTokenRepository):
    """In-memory device token store."""

    def __init__(self) -> None:
        self._store: dict[str, DeviceTokenEntity] = {}

    def register(self, entity: DeviceTokenEntity) -> DeviceTokenEntity:
        """Upsert by token value."""
        self._store[entity.token] = entity
        return entity

    def list_by_user(self, user_id: uuid.UUID) -> list[DeviceTokenEntity]:
        """Return all active tokens for a user."""
        return [t for t in self._store.values() if t.user_id == user_id and t.is_active]


class FakeJourneyRepository(IEventJourneyRepository):
    """In-memory journey and stage store."""

    def __init__(self) -> None:
        self._journeys: dict[uuid.UUID, EventJourneyEntity] = {}
        self._stages: dict[uuid.UUID, JourneyStageEntity] = {}

    def create(self, journey: EventJourneyEntity) -> EventJourneyEntity:
        """Store the journey and all its stages."""
        self._journeys[journey.event_id] = journey
        for stage in journey.stages:
            self._stages[stage.id] = stage
        return journey

    def get_by_event(self, event_id: uuid.UUID) -> EventJourneyEntity | None:
        """Return the journey for an event or None."""
        return self._journeys.get(event_id)

    def get_due_stages(self, as_of: datetime) -> list[JourneyStageEntity]:
        """Return pending stages whose trigger_at is on or before as_of."""
        return [s for s in self._stages.values() if s.status == "pending" and s.trigger_at <= as_of]

    def mark_stage_fired(self, stage_id: uuid.UUID) -> None:
        """Mark a stage as fired."""
        if stage_id in self._stages:
            self._stages[stage_id].status = "fired"
            self._stages[stage_id].fired_at = datetime.now(timezone.utc)
