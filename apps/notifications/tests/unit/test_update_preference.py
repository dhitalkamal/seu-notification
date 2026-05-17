"""Unit tests for UpdateNotificationPreferenceUseCase."""

from __future__ import annotations

import uuid

from apps.notifications.application.use_cases.update_preference import (
    UpdateNotificationPreferenceUseCase,
)
from apps.notifications.tests.unit.fakes import FakeNotificationPreferenceRepository


def test_update_preference_toggles_channels():
    """UpdatePreference stores the supplied channel toggles."""
    repo = FakeNotificationPreferenceRepository()
    user_id = uuid.uuid4()
    result = UpdateNotificationPreferenceUseCase(repo).execute(
        user_id=user_id,
        notification_type="event_reminder",
        email_enabled=False,
        push_enabled=True,
        sms_enabled=True,
        in_app_enabled=True,
    )
    assert result.email_enabled is False
    assert result.sms_enabled is True
    assert result.notification_type == "event_reminder"


def test_update_preference_creates_if_absent():
    """UpdatePreference creates the record when it does not yet exist."""
    repo = FakeNotificationPreferenceRepository()
    user_id = uuid.uuid4()
    result = UpdateNotificationPreferenceUseCase(repo).execute(
        user_id=user_id,
        notification_type="general",
        email_enabled=True,
        push_enabled=False,
        sms_enabled=False,
        in_app_enabled=True,
    )
    assert result.user_id == user_id
    assert result.push_enabled is False


def test_update_preference_overwrites_existing():
    """UpdatePreference replaces an existing record with new values."""
    repo = FakeNotificationPreferenceRepository()
    user_id = uuid.uuid4()
    UpdateNotificationPreferenceUseCase(repo).execute(
        user_id=user_id, notification_type="general",
        email_enabled=True, push_enabled=True, sms_enabled=False, in_app_enabled=True,
    )
    result = UpdateNotificationPreferenceUseCase(repo).execute(
        user_id=user_id, notification_type="general",
        email_enabled=False, push_enabled=False, sms_enabled=False, in_app_enabled=False,
    )
    assert result.email_enabled is False
    assert result.push_enabled is False
