"""Use case: deliver an email notification with primary/fallback sender strategy."""

from __future__ import annotations

import logging

from apps.notifications.domain.entities import EmailNotification
from apps.notifications.domain.exceptions import EmailDeliveryError
from apps.notifications.domain.repositories import IEmailSender

logger = logging.getLogger(__name__)


class SendEmailUseCase:
    """Deliver an email via the primary sender, falling back to the secondary on failure."""

    def __init__(self, primary: IEmailSender, fallback: IEmailSender) -> None:
        self._primary = primary
        self._fallback = fallback

    def execute(self, notification: EmailNotification) -> None:
        """
        Attempt delivery via primary, then fallback. Raises if both fail.

        @param notification - the email to deliver
        @raises EmailDeliveryError if both senders fail
        """
        try:
            self._primary.send(notification)
            return
        except EmailDeliveryError:
            logger.warning("Primary email sender failed, trying fallback.", exc_info=True)

        self._fallback.send(notification)
