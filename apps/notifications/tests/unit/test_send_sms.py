"""Unit tests for the SendSmsUseCase."""

from __future__ import annotations

import pytest

from apps.notifications.application.use_cases.send_sms import SendSmsUseCase
from apps.notifications.domain.entities import SmsNotification
from apps.notifications.domain.exceptions import SmsDeliveryError
from apps.notifications.domain.repositories import ISmsSender


class FakeSmsSender(ISmsSender):
    """Records sent SMS notifications. Always succeeds."""

    def __init__(self) -> None:
        self.sent: list[SmsNotification] = []

    def send(self, notification: SmsNotification) -> None:
        """Append to sent list."""
        self.sent.append(notification)


class AlwaysFailSmsSender(ISmsSender):
    """Always raises SmsDeliveryError."""

    def send(self, notification: SmsNotification) -> None:
        """Raise unconditionally."""
        raise SmsDeliveryError("Simulated SMS send failure.")


def _sms() -> SmsNotification:
    return SmsNotification(to_number="+447911123456", body="Your ticket is confirmed.")


def test_send_sms_delivers_via_sender() -> None:
    """SendSmsUseCase calls the sender with the notification."""
    sender = FakeSmsSender()
    SendSmsUseCase(sender).execute(_sms())
    assert len(sender.sent) == 1


def test_send_sms_passes_notification_unchanged() -> None:
    """The exact SmsNotification object is forwarded to the sender."""
    sender = FakeSmsSender()
    n = _sms()
    SendSmsUseCase(sender).execute(n)
    assert sender.sent[0] is n


def test_send_sms_raises_on_delivery_error() -> None:
    """SmsDeliveryError from the sender propagates to the caller."""
    with pytest.raises(SmsDeliveryError):
        SendSmsUseCase(AlwaysFailSmsSender()).execute(_sms())


def test_send_sms_to_number_and_body_preserved() -> None:
    """SmsNotification carries the to_number and body fields."""
    n = SmsNotification(to_number="+12025550100", body="Hello!")
    assert n.to_number == "+12025550100"
    assert n.body == "Hello!"
