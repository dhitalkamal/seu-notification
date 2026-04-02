"""Abstract interfaces for the notifications domain."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from apps.notifications.domain.entities import (
    DeviceTokenEntity,
    EmailNotification,
    EventJourneyEntity,
    JourneyStageEntity,
    NotificationEntity,
    NotificationPreferenceEntity,
)


class IEmailSender(ABC):
    """Delivers an EmailNotification via some transport (SendGrid, SMTP, etc.)."""

    @abstractmethod
    def send(self, notification: EmailNotification) -> None:
        """Send the email. Raises EmailDeliveryError if delivery fails."""
        ...


class INotificationRepository(ABC):
    """Persistence contract for Notification records."""

    @abstractmethod
    def create(self, entity: NotificationEntity) -> NotificationEntity: ...

    @abstractmethod
    def get_by_id(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity: ...

    @abstractmethod
    def list_by_user(self, user_id: uuid.UUID) -> list[NotificationEntity]: ...

    @abstractmethod
    def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationEntity: ...

    @abstractmethod
    def mark_all_read(self, user_id: uuid.UUID) -> int: ...

    @abstractmethod
    def unread_count(self, user_id: uuid.UUID) -> int: ...

    @abstractmethod
    def batch_create(self, entities: list[NotificationEntity]) -> list[NotificationEntity]: ...


class INotificationPreferenceRepository(ABC):
    """Persistence contract for NotificationPreference records."""

    @abstractmethod
    def get_or_create(self, user_id: uuid.UUID, notification_type: str) -> NotificationPreferenceEntity: ...

    @abstractmethod
    def upsert(self, entity: NotificationPreferenceEntity) -> NotificationPreferenceEntity: ...


class IDeviceTokenRepository(ABC):
    """Persistence contract for DeviceToken records."""

    @abstractmethod
    def register(self, entity: DeviceTokenEntity) -> DeviceTokenEntity: ...

    @abstractmethod
    def list_by_user(self, user_id: uuid.UUID) -> list[DeviceTokenEntity]: ...


class IEventJourneyRepository(ABC):
    """Persistence contract for event journey and stage records."""

    @abstractmethod
    def create(self, journey: "EventJourneyEntity") -> "EventJourneyEntity": ...

    @abstractmethod
    def get_by_event(self, event_id: uuid.UUID) -> "EventJourneyEntity | None": ...

    @abstractmethod
    def get_due_stages(self, as_of: "datetime") -> list["JourneyStageEntity"]: ...

    @abstractmethod
    def mark_stage_fired(self, stage_id: uuid.UUID) -> None: ...
