"""Domain errors raised by notifications use cases and never swallowed silently."""

from __future__ import annotations

from apps.common.api.exceptions import DomainError


class EmailDeliveryError(Exception):
    """All configured email senders failed to deliver the message."""


class NotificationNotFoundError(DomainError):
    """No notification matches the given identifier or the user does not own it."""

    http_status = 404
    code = "ERR_NOTIFICATION_NOT_FOUND"
