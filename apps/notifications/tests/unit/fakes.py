"""Hand-rolled fakes for notification interfaces."""

from __future__ import annotations

from apps.notifications.domain.entities import EmailNotification
from apps.notifications.domain.exceptions import EmailDeliveryError
from apps.notifications.domain.repositories import IEmailSender


class FakeEmailSender(IEmailSender):
    """Records sent notifications. Always succeeds."""

    def __init__(self) -> None:
        self.sent: list[EmailNotification] = []

    def send(self, notification: EmailNotification) -> None:
        """Append to sent list."""
        self.sent.append(notification)


class AlwaysFailEmailSender(IEmailSender):
    """Always raises EmailDeliveryError — simulates a completely broken transport."""

    def send(self, notification: EmailNotification) -> None:
        """Raise unconditionally."""
        raise EmailDeliveryError("Simulated send failure.")
