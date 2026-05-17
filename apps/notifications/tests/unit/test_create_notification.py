"""Unit tests for CreateNotificationUseCase."""

from __future__ import annotations

import uuid

from apps.notifications.application.use_cases.create_notification import CreateNotificationUseCase
from apps.notifications.tests.unit.fakes import (
    FakeNotificationRepository,
    FakePreferenceRepository,
    FakePublisher,
    make_preference,
)


def _uc(pref=None) -> tuple[CreateNotificationUseCase, FakePublisher]:
    publisher = FakePublisher()
    uc = CreateNotificationUseCase(
        notif_repo=FakeNotificationRepository(),
        pref_repo=FakePreferenceRepository(pref),
        publisher=publisher,
    )
    return uc, publisher


def test_in_app_notification_is_delivered():
    """In-app notifications are created with status=delivered immediately."""
    uc, publisher = _uc()
    result = uc.execute(
        user_id=uuid.uuid4(),
        notification_type="registration_confirmed",
        channel="in_app",
        title="You are registered",
        message="Your spot is confirmed.",
    )
    assert result.status == "delivered"
    assert len(publisher.published) == 0


def test_disabled_channel_creates_failed():
    """If the channel is disabled in preferences, status is set to failed."""
    pref = make_preference(in_app_enabled=False)
    uc, publisher = _uc(pref=pref)
    result = uc.execute(
        user_id=pref.user_id,
        notification_type="registration_confirmed",
        channel="in_app",
        title="Title",
        message="Message",
    )
    assert result.status == "failed"
    assert len(publisher.published) == 0


def test_email_notification_is_pending_and_published():
    """Email notifications are created with status=pending and published to the queue."""
    uc, publisher = _uc()
    result = uc.execute(
        user_id=uuid.uuid4(),
        notification_type="registration_confirmed",
        channel="email",
        title="Registration Confirmed",
        message="Your registration is confirmed.",
        data={"to_email": "user@example.com", "to_name": "Test User"},
    )
    assert result.status == "pending"
    assert len(publisher.published) == 1
    assert publisher.published[0]["to_email"] == "user@example.com"


def test_push_notification_is_pending_without_publish():
    """Push notifications are created with status=pending but no publisher call."""
    uc, publisher = _uc()
    result = uc.execute(
        user_id=uuid.uuid4(),
        notification_type="event_reminder",
        channel="push",
        title="Reminder",
        message="Your event starts tomorrow.",
    )
    assert result.status == "pending"
    assert len(publisher.published) == 0


def test_email_without_to_email_still_creates():
    """Email notification without to_email in data creates with empty string published."""
    uc, publisher = _uc()
    result = uc.execute(
        user_id=uuid.uuid4(),
        notification_type="registration_confirmed",
        channel="email",
        title="Title",
        message="Message",
        data={},
    )
    assert result.status == "pending"
    assert publisher.published[0]["to_email"] == ""
