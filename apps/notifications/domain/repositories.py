"""Abstract interfaces for the notifications domain."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from apps.notifications.domain.entities import (
    EmailNotification,
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
    """Persistence contract for Notification aggregates."""

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
    def update_status(self, notification_id: uuid.UUID, status: str) -> None: ...


class INotificationPreferenceRepository(ABC):
    """Persistence contract for notification preferences."""

    @abstractmethod
    def get_or_default(
        self, user_id: uuid.UUID, notification_type: str
    ) -> NotificationPreferenceEntity: ...


class IPublisher(ABC):
    """Port for publishing notification delivery jobs to the message queue."""

    @abstractmethod
    def publish(
        self,
        *,
        notification_id: uuid.UUID,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
    ) -> None: ...
