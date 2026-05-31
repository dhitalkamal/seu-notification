"""Unit tests for BatchCreateNotificationsUseCase."""

from __future__ import annotations

import uuid

from apps.notifications.application.use_cases.batch_create_notifications import (
    BatchCreateNotificationsUseCase,
)
from apps.notifications.tests.unit.fakes import (
    FakeNotificationPreferenceRepository,
    FakeNotificationRepository,
    make_preference,
)


def _user_ids(n: int) -> list[uuid.UUID]:
    return [uuid.uuid4() for _ in range(n)]


def test_batch_creates_one_notification_per_user():
    """Each user in the batch receives exactly one notification."""
    users = _user_ids(3)
    notif_repo = FakeNotificationRepository()
    pref_repo = FakeNotificationPreferenceRepository()

    result = BatchCreateNotificationsUseCase(notif_repo, pref_repo).execute(
        user_ids=users,
        notification_type="event_reminder",
        channel="in_app",
        title="Reminder",
        message="Your event starts soon.",
    )

    assert len(result) == 3
    assert all(n.status == "delivered" for n in result)


def test_batch_skips_disabled_channel():
    """Users who disabled the channel do not get a notification."""
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    notif_repo = FakeNotificationRepository()
    pref_repo = FakeNotificationPreferenceRepository(
        preferences=[
            make_preference(
                user_id=user_b,
                notification_type="event_reminder",
                in_app_enabled=False,
            )
        ]
    )

    result = BatchCreateNotificationsUseCase(notif_repo, pref_repo).execute(
        user_ids=[user_a, user_b],
        notification_type="event_reminder",
        channel="in_app",
        title="Reminder",
        message="Your event starts soon.",
    )

    # user_b disabled in_app, so only user_a gets the notification
    assert len(result) == 1
    assert result[0].user_id == user_a


def test_batch_max_1000_users():
    """Batch is capped at 1,000 users per call."""
    users = _user_ids(1500)
    notif_repo = FakeNotificationRepository()
    pref_repo = FakeNotificationPreferenceRepository()

    result = BatchCreateNotificationsUseCase(notif_repo, pref_repo).execute(
        user_ids=users,
        notification_type="event_reminder",
        channel="in_app",
        title="Test",
        message="Test message.",
    )

    assert len(result) == 1000
