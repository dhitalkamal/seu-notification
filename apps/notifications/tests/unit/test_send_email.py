"""Unit tests for the SendEmailUseCase."""

from __future__ import annotations

import pytest

from apps.notifications.application.use_cases.send_email import SendEmailUseCase
from apps.notifications.domain.entities import EmailNotification
from apps.notifications.domain.exceptions import EmailDeliveryError
from apps.notifications.tests.unit.fakes import AlwaysFailEmailSender, FakeEmailSender


def _notification() -> EmailNotification:
    return EmailNotification(
        to_email="user@example.com",
        to_name="Test User",
        subject="Verify your email",
        html_body="<p>Your OTP is <strong>ABCD1234</strong></p>",
    )


def test_send_email_delivers_via_primary():
    """Uses the primary sender when it succeeds."""
    primary = FakeEmailSender()
    fallback = FakeEmailSender()

    SendEmailUseCase(primary, fallback).execute(_notification())

    assert len(primary.sent) == 1
    assert len(fallback.sent) == 0


def test_send_email_falls_back_when_primary_fails():
    """Switches to the fallback sender when the primary raises EmailDeliveryError."""
    fallback = FakeEmailSender()

    SendEmailUseCase(AlwaysFailEmailSender(), fallback).execute(_notification())

    assert len(fallback.sent) == 1


def test_send_email_raises_when_both_fail():
    """Raises EmailDeliveryError when both primary and fallback fail."""
    with pytest.raises(EmailDeliveryError):
        SendEmailUseCase(AlwaysFailEmailSender(), AlwaysFailEmailSender()).execute(_notification())


def test_send_email_passes_notification_unchanged():
    """The exact notification object is forwarded to the sender."""
    sender = FakeEmailSender()
    n = _notification()

    SendEmailUseCase(sender, FakeEmailSender()).execute(n)

    assert sender.sent[0] is n
