"""SendGrid email sender, primary transport."""

from __future__ import annotations

import logging

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from apps.notifications.domain.entities import EmailNotification
from apps.notifications.domain.exceptions import EmailDeliveryError
from apps.notifications.domain.repositories import IEmailSender

logger = logging.getLogger(__name__)


class SendGridEmailSender(IEmailSender):
    """Delivers email via the SendGrid API."""

    def send(self, notification: EmailNotification) -> None:
        """Build a Mail object and submit it to SendGrid. Raises EmailDeliveryError on failure."""
        message = Mail(
            from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=notification.to_email,
            subject=notification.subject,
            html_content=notification.html_body,
        )
        try:
            client = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = client.send(message)
            if response.status_code >= 400:
                raise EmailDeliveryError(f"SendGrid returned HTTP {response.status_code}.")
        except EmailDeliveryError:
            raise
        except Exception as exc:
            logger.error("SendGrid send failed.", exc_info=True)
            raise EmailDeliveryError("SendGrid send failed.") from exc
