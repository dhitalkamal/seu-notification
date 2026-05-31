"""Use case: register or reactivate a device push token."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from apps.notifications.domain.entities import DeviceTokenEntity
from apps.notifications.domain.repositories import IDeviceTokenRepository


class RegisterDeviceTokenUseCase:
    """Upsert a device token — update_or_create by token value."""

    def __init__(self, device_token_repo: IDeviceTokenRepository) -> None:
        self._tokens = device_token_repo

    def execute(self, *, user_id: uuid.UUID, token: str, platform: str) -> DeviceTokenEntity:
        """
        Register a device token for push notifications.

        If the token already exists it is reassigned to user_id and reactivated.

        @param user_id - the user registering the token
        @param token - device push token (max 512 chars, unique)
        @param platform - ios | android | web
        """
        entity = DeviceTokenEntity(
            id=uuid.uuid4(),
            user_id=user_id,
            token=token,
            platform=platform,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        return self._tokens.register(entity)
