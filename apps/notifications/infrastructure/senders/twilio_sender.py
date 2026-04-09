"""Twilio SMS sender — production transport for outbound SMS."""

from __future__ import annotations

import logging

from django.conf import settings

from apps.notifications.domain.entities import SmsNotification
from apps.notifications.domain.exceptions import SmsDeliveryError
from apps.notifications.domain.repositories import ISmsSender

logger = logging.getLogger(__name__)


class TwilioSmsSender(ISmsSender):
    """Delivers SMS via the Twilio REST API."""

    def send(self, notification: SmsNotification) -> None:
        """Submit the message to Twilio. Raises SmsDeliveryError on failure."""
        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=notification.body,
                from_=settings.TWILIO_FROM_NUMBER,
                to=notification.to_number,
            )
        except Exception as exc:
            logger.error("Twilio SMS send failed.", exc_info=True)
            raise SmsDeliveryError("Twilio SMS send failed.") from exc
