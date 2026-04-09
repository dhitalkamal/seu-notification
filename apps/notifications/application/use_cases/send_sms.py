"""Use case: deliver an SMS notification via the configured sender."""

from __future__ import annotations

from apps.notifications.domain.entities import SmsNotification
from apps.notifications.domain.repositories import ISmsSender


class SendSmsUseCase:
    """Deliver an SMS via the injected sender."""

    def __init__(self, sender: ISmsSender) -> None:
        self._sender = sender

    def execute(self, notification: SmsNotification) -> None:
        """Call the sender with the notification. Propagates SmsDeliveryError on failure."""
        self._sender.send(notification)
