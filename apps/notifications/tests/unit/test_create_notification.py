"""Unit tests for CreateNotificationUseCase."""

from __future__ import annotations

import uuid

from apps.notifications.application.use_cases.create_notification import CreateNotificationUseCase
from apps.notifications.tests.unit.fakes import (
    FakeNotificationPreferenceRepository,
    FakeNotificationRepository,
)


def test_create_notification_in_app_channel():
    """Creating an in_app notification stores it with status=delivered."""
    repo = FakeNotificationRepository()
    pref_repo = FakeNotificationPreferenceRepository()
    user_id = uuid.uuid4()
    entity = CreateNotificationUseCase(repo, pref_repo).execute(
        user_id=user_id,
        notification_type="general",
        channel="in_app",
        title="Welcome",
        message="Welcome to Sansaar!",
    )
    assert entity.status == "delivered"
    assert entity.is_read is False
    assert entity.user_id == user_id


def test_create_notification_respects_in_app_preference_disabled():
    """When in_app_enabled=False, notification is created with status=failed."""
    repo = FakeNotificationRepository()
    pref_repo = FakeNotificationPreferenceRepository()
    user_id = uuid.uuid4()
    pref = pref_repo.get_or_create(user_id, "general")
    pref.in_app_enabled = False
    pref_repo.upsert(pref)

    entity = CreateNotificationUseCase(repo, pref_repo).execute(
        user_id=user_id,
        notification_type="general",
        channel="in_app",
        title="Hello",
        message="Test",
    )
    assert entity.status == "failed"


def test_create_notification_stores_data_payload():
    """Extra data dict is persisted on the notification."""
    repo = FakeNotificationRepository()
    pref_repo = FakeNotificationPreferenceRepository()
    entity = CreateNotificationUseCase(repo, pref_repo).execute(
        user_id=uuid.uuid4(),
        notification_type="registration_confirmed",
        channel="in_app",
        title="Registration confirmed",
        message="Your ticket is ready.",
        data={"registration_id": "abc123"},
    )
    assert entity.data == {"registration_id": "abc123"}
