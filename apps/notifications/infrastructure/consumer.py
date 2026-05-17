"""RabbitMQ consumer for incoming IAM notification events."""

from __future__ import annotations

import json
import logging
import os

import pika
from django.conf import settings

from apps.notifications.application.use_cases.send_email import SendEmailUseCase
from apps.notifications.domain.entities import EmailNotification
from apps.notifications.infrastructure.senders.gmail_sender import GmailEmailSender
from apps.notifications.infrastructure.senders.mailhog_sender import MailHogEmailSender
from apps.notifications.infrastructure.senders.sendgrid_sender import SendGridEmailSender

logger = logging.getLogger(__name__)

_EXCHANGE = "sansaar"
_EXCHANGE_TYPE = "topic"
_QUEUE = "notifications.iam"
_ROUTING_KEY = "iam.*"

# Explicit opt-in for local mail capture — set USE_MAILHOG=true in env to use MailHog.
_USE_MAILHOG = os.getenv("USE_MAILHOG", "false").strip().lower() == "true"


def _send(notification: EmailNotification) -> None:
    """Route to MailHog when USE_MAILHOG=true, otherwise SendGrid with Gmail fallback."""
    if _USE_MAILHOG:
        MailHogEmailSender().send(notification)
    else:
        SendEmailUseCase(SendGridEmailSender(), GmailEmailSender()).execute(notification)


def _build_email_verification(payload: dict) -> EmailNotification:
    """Build the email verification message from the event payload."""
    otp = payload["otp"]
    first_name = payload.get("first_name", "there")
    html = (
        f"<p>Hi {first_name},</p>"
        f"<p>Use the code below to verify your Sansaar account. It expires in 10 minutes.</p>"
        f"<h2 style='letter-spacing:4px;font-family:monospace'>{otp}</h2>"
        f"<p>If you did not create an account, you can ignore this email.</p>"
    )
    return EmailNotification(
        to_email=payload["email"],
        to_name=first_name,
        subject="Verify your Sansaar account",
        html_body=html,
    )


def _build_password_reset(payload: dict) -> EmailNotification:
    """Build the password reset message from the event payload."""
    otp = payload["otp"]
    first_name = payload.get("first_name", "there")
    html = (
        f"<p>Hi {first_name},</p>"
        f"<p>Use the code below to reset your Sansaar password. It expires in 10 minutes.</p>"
        f"<h2 style='letter-spacing:4px;font-family:monospace'>{otp}</h2>"
        f"<p>If you did not request a password reset, you can ignore this email.</p>"
    )
    return EmailNotification(
        to_email=payload["email"],
        to_name=first_name,
        subject="Reset your Sansaar password",
        html_body=html,
    )


def _build_password_changed(payload: dict) -> EmailNotification:
    """Build the password-changed security alert."""
    first_name = payload.get("first_name", "there")
    ip = payload.get("ip_address", "unknown")
    html = (
        f"<p>Hi {first_name},</p>"
        f"<p>Your Sansaar password was just changed.</p>"
        f"<p>IP address: <strong>{ip}</strong></p>"
        f"<p>If this was you, no action is needed. "
        f"If you did not change your password, reset it immediately.</p>"
    )
    return EmailNotification(
        to_email=payload["email"],
        to_name=first_name,
        subject="Your Sansaar password was changed",
        html_body=html,
    )


def _build_mfa_enabled(payload: dict) -> EmailNotification:
    """Build the MFA-enabled security alert."""
    first_name = payload.get("first_name", "there")
    ip = payload.get("ip_address", "unknown")
    html = (
        f"<p>Hi {first_name},</p>"
        f"<p>Two-factor authentication (MFA) has been enabled on your Sansaar account.</p>"
        f"<p>IP address: <strong>{ip}</strong></p>"
        f"<p>If this was not you, secure your account immediately by changing your password.</p>"
    )
    return EmailNotification(
        to_email=payload["email"],
        to_name=first_name,
        subject="MFA enabled on your Sansaar account",
        html_body=html,
    )


def _build_mfa_disabled(payload: dict) -> EmailNotification:
    """Build the MFA-disabled security alert."""
    first_name = payload.get("first_name", "there")
    ip = payload.get("ip_address", "unknown")
    html = (
        f"<p>Hi {first_name},</p>"
        f"<p><strong>Warning:</strong> Two-factor authentication (MFA) has been "
        f"<strong>disabled</strong> on your Sansaar account.</p>"
        f"<p>IP address: <strong>{ip}</strong></p>"
        f"<p>If this was not you, re-enable MFA and change your password immediately.</p>"
    )
    return EmailNotification(
        to_email=payload["email"],
        to_name=first_name,
        subject="MFA disabled on your Sansaar account",
        html_body=html,
    )


def _build_account_locked(payload: dict) -> EmailNotification:
    """Build the account-locked security alert."""
    first_name = payload.get("first_name", "there")
    ip = payload.get("ip_address", "unknown")
    locked_until = payload.get("locked_until", "shortly")
    html = (
        f"<p>Hi {first_name},</p>"
        f"<p>Your Sansaar account has been temporarily locked due to multiple failed login attempts.</p>"
        f"<p>IP address: <strong>{ip}</strong></p>"
        f"<p>The account will unlock at <strong>{locked_until}</strong>.</p>"
        f"<p>If this was not you, reset your password immediately after the lockout expires.</p>"
    )
    return EmailNotification(
        to_email=payload["email"],
        to_name=first_name,
        subject="Your Sansaar account has been temporarily locked",
        html_body=html,
    )


def _build_registration_confirmed(payload: dict) -> EmailNotification | None:
    """Build the registration confirmation email. Returns None when email is absent."""
    email = payload.get("email", "")
    if not email:
        logger.info(
            "participation.registration.created missing email — skipping email send. "
            "user_id=%s",
            payload.get("user_id"),
        )
        return None
    code = payload.get("registration_code", "")
    name = payload.get("first_name", "there")
    html = (
        f"<p>Hi {name},</p>"
        f"<p>You're registered! Here is your entry code:</p>"
        f"<h2 style='letter-spacing:4px;font-family:monospace;font-size:28px'>{code}</h2>"
        f"<p>Show this code (or its QR) at the entrance.</p>"
        f"<p>See your full ticket at <a href='https://sansaar.app/tickets'>My Tickets</a>.</p>"
    )
    return EmailNotification(
        to_email=email, to_name=name,
        subject="You're registered! Your entry code inside",
        html_body=html,
    )


def _build_waitlist_promoted(payload: dict) -> EmailNotification | None:
    """Build the waitlist promotion email. Returns None when email is absent."""
    email = payload.get("email", "")
    if not email:
        logger.info(
            "participation.waitlist.promoted missing email — skipping email send. "
            "user_id=%s",
            payload.get("user_id"),
        )
        return None
    code = payload.get("registration_code", "")
    name = payload.get("first_name", "there")
    html = (
        f"<p>Hi {name},</p>"
        f"<p>Good news — a spot opened up and you've been moved off the waitlist!</p>"
        f"<p>Your registration code:</p>"
        f"<h2 style='letter-spacing:4px;font-family:monospace;font-size:28px'>{code}</h2>"
        f"<p>See your full ticket at <a href='https://sansaar.app/tickets'>My Tickets</a>.</p>"
    )
    return EmailNotification(
        to_email=email, to_name=name,
        subject="Great news — you're off the waitlist!",
        html_body=html,
    )


_HANDLERS = {
    "iam.email_verification_requested": _build_email_verification,
    "iam.password_reset_requested": _build_password_reset,
    "iam.password_changed": _build_password_changed,
    "iam.mfa_enabled": _build_mfa_enabled,
    "iam.mfa_disabled": _build_mfa_disabled,
    "iam.account_locked": _build_account_locked,
    "participation.registration.created": _build_registration_confirmed,
    "participation.waitlist.promoted": _build_waitlist_promoted,
}


def _handle_message(
    channel: pika.channel.Channel,
    method: pika.spec.Basic.Deliver,
    _props: object,
    body: bytes,
) -> None:
    """Route and process a single message from the queue."""
    try:
        payload = json.loads(body)
        event_name = method.routing_key
        builder = _HANDLERS.get(event_name)
        if builder is None:
            logger.warning("No handler for event %s, skipping.", event_name)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        notification = builder(payload)
        if notification is not None:
            _send(notification)
            logger.info("Email sent for event %s to %s.", event_name, payload.get("email"))
        else:
            logger.debug("Builder returned None for event %s — acking without send.", event_name)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        logger.error("Failed to process message for event %s.", method.routing_key, exc_info=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consuming() -> None:
    """Connect to RabbitMQ, declare the topology, and block on message consumption."""
    params = pika.URLParameters(settings.RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange=_EXCHANGE, exchange_type=_EXCHANGE_TYPE, durable=True)
    channel.queue_declare(queue=_QUEUE, durable=True)
    # bind to both IAM and participation events so one consumer handles all email triggers
    channel.queue_bind(queue=_QUEUE, exchange=_EXCHANGE, routing_key=_ROUTING_KEY)
    channel.queue_bind(queue=_QUEUE, exchange=_EXCHANGE, routing_key="participation.#")
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=_QUEUE, on_message_callback=_handle_message)

    logger.info(
        "Notification consumer started. Bound to %s and participation.#.", _ROUTING_KEY
    )
    channel.start_consuming()
