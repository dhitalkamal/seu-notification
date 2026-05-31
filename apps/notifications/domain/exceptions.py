"""Domain errors raised by notifications use cases and never swallowed silently."""

from __future__ import annotations

from apps.common.api.exceptions import DomainError


class EmailDeliveryError(Exception):
    """All configured email senders failed to deliver the message."""


class NotificationNotFoundError(DomainError):
    """No notification matches the given identifier."""

    http_status = 404
    code = "ERR_NOTIFICATION_NOT_FOUND"


class DeviceTokenAlreadyExistsError(DomainError):
    """A device token with this value is already registered."""

    http_status = 409
    code = "ERR_DEVICE_TOKEN_EXISTS"
