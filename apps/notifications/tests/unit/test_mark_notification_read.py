"""Unit tests for MarkNotificationReadUseCase and MarkAllReadUseCase."""

from __future__ import annotations

import uuid

import pytest

from apps.notifications.application.use_cases.mark_all_read import MarkAllReadUseCase
from apps.notifications.application.use_cases.mark_notification_read import (
    MarkNotificationReadUseCase,
)
from apps.notifications.domain.exceptions import NotificationNotFoundError
from apps.notifications.tests.unit.fakes import FakeNotificationRepository, make_notification


def test_mark_read_sets_is_read_true():
    """Marking a notification read sets is_read=True and populates read_at."""
    user_id = uuid.uuid4()
    notif = make_notification(user_id=user_id, is_read=False)
    repo = FakeNotificationRepository([notif])
    result = MarkNotificationReadUseCase(repo).execute(
        notification_id=notif.id, user_id=user_id
    )
    assert result.is_read is True
    assert result.read_at is not None


def test_mark_read_wrong_user_raises():
    """Raises NotificationNotFoundError when user does not own the notification."""
    notif = make_notification(is_read=False)
    repo = FakeNotificationRepository([notif])
    with pytest.raises(NotificationNotFoundError):
        MarkNotificationReadUseCase(repo).execute(
            notification_id=notif.id, user_id=uuid.uuid4()
        )


def test_mark_read_already_read_is_noop():
    """Marking an already-read notification is a no-op — read_at is not updated."""
    from datetime import datetime, timezone
    original_read_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user_id = uuid.uuid4()
    notif = make_notification(user_id=user_id, is_read=True, read_at=original_read_at)
    repo = FakeNotificationRepository([notif])
    result = MarkNotificationReadUseCase(repo).execute(
        notification_id=notif.id, user_id=user_id
    )
    assert result.read_at == original_read_at


def test_mark_all_read_updates_all_unread():
    """Mark all unread notifications for the user as read, return count."""
    user_id = uuid.uuid4()
    unread = [make_notification(user_id=user_id, is_read=False) for _ in range(4)]
    already_read = make_notification(user_id=user_id, is_read=True)
    other_user = make_notification(is_read=False)
    repo = FakeNotificationRepository(unread + [already_read, other_user])
    count = MarkAllReadUseCase(repo).execute(user_id=user_id)
    assert count == 4


def test_mark_all_read_returns_zero_when_none_unread():
    """Returns 0 when all notifications are already read."""
    user_id = uuid.uuid4()
    repo = FakeNotificationRepository([make_notification(user_id=user_id, is_read=True)])
    count = MarkAllReadUseCase(repo).execute(user_id=user_id)
    assert count == 0
