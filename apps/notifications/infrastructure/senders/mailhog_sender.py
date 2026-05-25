"""MailHog SMTP sender for local development — captures all mail at http://localhost:8025."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings

from apps.notifications.domain.entities import EmailNotification
from apps.notifications.domain.exceptions import EmailDeliveryError
from apps.notifications.domain.repositories import IEmailSender

logger = logging.getLogger(__name__)

_SMTP_HOST = "mailhog"
_SMTP_PORT = 1025


class MailHogEmailSender(IEmailSender):
    """Delivers email to MailHog over plain SMTP with no auth. View captured mail at :8025."""

    def send(self, notification: EmailNotification) -> None:
        """Connect to MailHog and hand off the message. Raises EmailDeliveryError on failure."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = notification.subject
        msg["From"] = f"{settings.SENDGRID_FROM_NAME} <{settings.GMAIL_ADDRESS or 'noreply@sansaar.local'}>"
        msg["To"] = notification.to_email
        msg.attach(MIMEText(notification.html_body, "html"))

        try:
            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
                server.sendmail(msg["From"], notification.to_email, msg.as_string())
            logger.info("MailHog: delivered '%s' to %s", notification.subject, notification.to_email)
        except Exception as exc:
            logger.error("MailHog send failed.", exc_info=True)
            raise EmailDeliveryError("MailHog send failed.") from exc
