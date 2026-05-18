"""Gmail SMTP email sender, fallback transport."""

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

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


class GmailEmailSender(IEmailSender):
    """Delivers email via Gmail SMTP on port 587 using STARTTLS and an app password."""

    def send(self, notification: EmailNotification) -> None:
        """Open a STARTTLS connection to Gmail and send. Raises EmailDeliveryError on failure."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = notification.subject
        msg["From"] = f"{settings.SENDGRID_FROM_NAME} <{settings.GMAIL_ADDRESS}>"
        msg["To"] = notification.to_email
        msg.attach(MIMEText(notification.html_body, "html"))

        try:
            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD)
                server.sendmail(settings.GMAIL_ADDRESS, notification.to_email, msg.as_string())
        except Exception as exc:
            logger.error("Gmail send failed.", exc_info=True)
            raise EmailDeliveryError("Gmail send failed.") from exc
