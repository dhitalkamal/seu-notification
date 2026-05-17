"""Unit tests for MarkAllReadUseCase."""

from __future__ import annotations

import uuid

from apps.notifications.application.use_cases.mark_all_read import MarkAllReadUseCase
from apps.notifications.tests.unit.fakes import FakeNotificationRepository, make_notification


def _uc(notifications=None) -> MarkAllReadUseCase:
    return MarkAllReadUseCase(FakeNotificationRepository(notifications or []))


def test_mark_all_read_returns_count_of_newly_read():
    """Returns the count of notifications that were just marked as read."""
    user_id = uuid.uuid4()
    n1 = make_notification(user_id=user_id, is_read=False)
    n2 = make_notification(user_id=user_id, is_read=False)
    n3 = make_notification(user_id=user_id, is_read=True)
    count = _uc([n1, n2, n3]).execute(user_id=user_id)
    assert count == 2


def test_mark_all_read_returns_zero_when_none_unread():
    """Returns 0 when the user has no unread notifications."""
    count = _uc().execute(user_id=uuid.uuid4())
    assert count == 0
