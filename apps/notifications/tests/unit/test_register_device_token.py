"""Unit tests for RegisterDeviceTokenUseCase."""

from __future__ import annotations

import uuid

from apps.notifications.application.use_cases.register_device_token import (
    RegisterDeviceTokenUseCase,
)
from apps.notifications.tests.unit.fakes import FakeDeviceTokenRepository


def test_register_device_token_stores_token():
    """Registering a token persists it with is_active=True."""
    repo = FakeDeviceTokenRepository()
    user_id = uuid.uuid4()
    entity = RegisterDeviceTokenUseCase(repo).execute(
        user_id=user_id, token="abc123token", platform="ios"
    )
    assert entity.token == "abc123token"
    assert entity.platform == "ios"
    assert entity.is_active is True
    assert entity.user_id == user_id


def test_register_device_token_same_token_updates_user():
    """Re-registering the same token updates the user association (upsert)."""
    repo = FakeDeviceTokenRepository()
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    RegisterDeviceTokenUseCase(repo).execute(user_id=user_a, token="shared_token", platform="web")
    result = RegisterDeviceTokenUseCase(repo).execute(
        user_id=user_b, token="shared_token", platform="web"
    )
    assert result.user_id == user_b
    assert len(repo._store) == 1
