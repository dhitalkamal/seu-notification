"""Pure Python domain entities for the notifications module with no framework dependencies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmailNotification:
    """Represents a single outbound email to be delivered."""

    to_email: str
    to_name: str
    subject: str
    html_body: str
