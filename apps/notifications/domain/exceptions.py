"""Domain errors raised by notifications use cases and never swallowed silently."""

from __future__ import annotations


class EmailDeliveryError(Exception):
    """All configured email senders failed to deliver the message."""
