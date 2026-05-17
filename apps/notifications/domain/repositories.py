"""Abstract interfaces for the notifications domain."""

from __future__ import annotations

from abc import ABC, abstractmethod

from apps.notifications.domain.entities import EmailNotification


class IEmailSender(ABC):
    """Delivers an EmailNotification via some transport (SendGrid, SMTP, etc.)."""

    @abstractmethod
    def send(self, notification: EmailNotification) -> None:
        """Send the email. Raises EmailDeliveryError if delivery fails."""
        ...
