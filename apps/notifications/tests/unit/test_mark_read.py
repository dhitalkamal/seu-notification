"""Unit tests for MarkNotificationReadUseCase."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from apps.notifications.application.use_cases.mark_read import MarkNotificationReadUseCase
from apps.notifications.domain.exceptions import NotificationNotFoundError
from apps.notifications.tests.unit.fakes import FakeNotificationRepository, make_notification


def _uc(notifications=None) -> MarkNotificationReadUseCase:
    return MarkNotificationReadUseCase(FakeNotificationRepository(notifications or []))


def test_mark_read_sets_is_read_and_read_at():
    """Marking an unread notification sets is_read=True and populates read_at."""
    user_id = uuid.uuid4()
    notif = make_notification(user_id=user_id, is_read=False)
    result = _uc([notif]).execute(notification_id=notif.id, user_id=user_id)
    assert result.is_read is True
    assert result.read_at is not None


def test_mark_read_is_idempotent():
    """Marking an already-read notification returns it with unchanged read_at."""
    user_id = uuid.uuid4()
    original_time = datetime.now(timezone.utc)
    notif = make_notification(user_id=user_id, is_read=True, read_at=original_time)
    result = _uc([notif]).execute(notification_id=notif.id, user_id=user_id)
    assert result.read_at == original_time


def test_mark_read_wrong_owner_raises():
    """Marking a notification you do not own raises NotificationNotFoundError."""
    notif = make_notification(user_id=uuid.uuid4(), is_read=False)
    with pytest.raises(NotificationNotFoundError):
        _uc([notif]).execute(notification_id=notif.id, user_id=uuid.uuid4())
