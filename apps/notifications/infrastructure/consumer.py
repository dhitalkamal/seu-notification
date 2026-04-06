"""RabbitMQ consumer for incoming IAM and participation notification events."""

from __future__ import annotations

import json
import logging
import os
import uuid

import pika
from django.conf import settings

from apps.notifications.application.use_cases.send_email import SendEmailUseCase
from apps.notifications.domain.entities import EmailNotification
from apps.notifications.infrastructure.repositories import DjangoDeviceTokenRepository
from apps.notifications.infrastructure.senders.fcm_sender import send_push_multicast
from apps.notifications.infrastructure.senders.gmail_sender import GmailEmailSender
from apps.notifications.infrastructure.senders.mailhog_sender import MailHogEmailSender
from apps.notifications.infrastructure.senders.sendgrid_sender import SendGridEmailSender

logger = logging.getLogger(__name__)

_EXCHANGE = "sansaar"
_EXCHANGE_TYPE = "topic"
_QUEUE = "notifications.iam"
_ROUTING_KEY = "iam.*"

# Explicit opt-in for local mail capture - set USE_MAILHOG=true in env to use MailHog.
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
        "<p>Your Sansaar account has been temporarily locked "
        "due to multiple failed login attempts.</p>"
        f"<p>IP address: <strong>{ip}</strong></p>"
        f"<p>The account will unlock at <strong>{locked_until}</strong>.</p>"
        "<p>If this was not you, reset your password immediately "
        "after the lockout expires.</p>"
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
            "participation.registration.created missing email - skipping email send. user_id=%s",
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
        to_email=email,
        to_name=name,
        subject="You're registered! Your entry code inside",
        html_body=html,
    )


def _build_waitlist_promoted(payload: dict) -> EmailNotification | None:
    """Build the waitlist promotion email. Returns None when email is absent."""
    email = payload.get("email", "")
    if not email:
        logger.info(
            "participation.waitlist.promoted missing email - skipping email send. user_id=%s",
            payload.get("user_id"),
        )
        return None
    code = payload.get("registration_code", "")
    name = payload.get("first_name", "there")
    html = (
        f"<p>Hi {name},</p>"
        f"<p>Good news - a spot opened up and you have been moved off the waitlist!</p>"
        f"<p>Your registration code:</p>"
        f"<h2 style='letter-spacing:4px;font-family:monospace;font-size:28px'>{code}</h2>"
        f"<p>See your full ticket at <a href='https://sansaar.app/tickets'>My Tickets</a>.</p>"
    )
    return EmailNotification(
        to_email=email,
        to_name=name,
        subject="Great news - you're off the waitlist!",
        html_body=html,
    )


def _build_waitlist_joined(payload: dict) -> EmailNotification | None:
    """Build the waitlist confirmation email. Returns None when email is absent."""
    email = payload.get("email", "")
    if not email:
        logger.info(
            "participation.waitlist.joined missing email - skipping email send. user_id=%s",
            payload.get("user_id"),
        )
        return None
    position = payload.get("position", "?")
    name = payload.get("first_name", "there")
    html = (
        f"<p>Hi {name},</p>"
        f"<p>The event is currently full, but you've been added to the waitlist "
        f"at <strong>position #{position}</strong>.</p>"
        f"<p>We'll notify you immediately if a spot opens up.</p>"
        f"<p>You can view your waitlist status at "
        f"<a href='https://sansaar.app/tickets'>My Tickets</a>.</p>"
    )
    return EmailNotification(
        to_email=email,
        to_name=name,
        subject="You're on the waitlist!",
        html_body=html,
    )


def _build_registration_cancelled(payload: dict) -> EmailNotification | None:
    """Build the cancellation confirmation email. Returns None when email absent."""
    email = payload.get("email", "")
    if not email:
        logger.info(
            "participation.registration.cancelled missing email - skipping. user_id=%s",
            payload.get("user_id"),
        )
        return None
    code = payload.get("registration_code", "")
    name = payload.get("first_name", "there")
    html = (
        f"<p>Hi {name},</p><p>Your registration ({code}) has been cancelled.</p><p>If you did not request this, please contact support.</p>"
    )
    return EmailNotification(
        to_email=email,
        to_name=name,
        subject="Your registration has been cancelled",
        html_body=html,
    )


_PUSH_TITLES = {
    "participation.registration.created": "Registration confirmed!",
    "participation.waitlist.joined": "You're on the waitlist",
    "participation.waitlist.promoted": "You are off the waitlist!",
    "participation.registration.cancelled": "Registration cancelled",
}

_PUSH_BODIES = {
    "participation.registration.created": "Your entry code is ready. Check My Tickets.",
    "participation.waitlist.joined": "We'll notify you when a spot opens up.",
    "participation.waitlist.promoted": "A spot opened up. Your entry code is in My Tickets.",
    "participation.registration.cancelled": "Your registration has been cancelled.",
}


def _build_org_created(payload: dict) -> EmailNotification:
    """Notify the org creator that their application is under review."""
    email = payload.get("contact_email", "")
    name = payload.get("org_name", "your organization")
    html = (
        f"<p>Hi,</p>"
        f"<p>Your organization <strong>{name}</strong> has been submitted for review.</p>"
        f"<p>Our team will review your application and documents within 24-48 hours. "
        f"You will receive an email once the review is complete.</p>"
        f"<p>Thank you for joining Sansaar!</p>"
    )
    return EmailNotification(
        to_email=email,
        to_name=name,
        subject=f"Organization submitted for review - {name}",
        html_body=html,
    )


def _build_org_approved(payload: dict) -> EmailNotification:
    """Notify the org that they have been approved."""
    email = payload.get("contact_email", "")
    name = payload.get("org_name", "your organization")
    html = (
        f"<p>Great news!</p>"
        f"<p>Your organization <strong>{name}</strong> has been approved and is now active on Sansaar.</p>"
        f"<p>You can now create events, manage your team, and start accepting registrations.</p>"
        f"<p>Get started from your <a href='http://localhost:5173/dashboard'>organization dashboard</a>.</p>"
    )
    return EmailNotification(
        to_email=email,
        to_name=name,
        subject=f"Organization approved - {name}",
        html_body=html,
    )


def _build_org_rejected(payload: dict) -> EmailNotification:
    """Notify the org that their application was rejected."""
    email = payload.get("contact_email", "")
    name = payload.get("org_name", "your organization")
    html = (
        f"<p>Hi,</p>"
        f"<p>Unfortunately, your organization <strong>{name}</strong> was not approved at this time.</p>"
        f"<p>This may be due to incomplete documentation or information. "
        f"Please review your submission, update your documents, and resubmit for review.</p>"
        f"<p>If you have questions, please contact our support team.</p>"
    )
    return EmailNotification(
        to_email=email,
        to_name=name,
        subject=f"Organization review update - {name}",
        html_body=html,
    )


def _send_push_for_participation(event_name: str, payload: dict) -> None:
    """Send FCM push notifications to all active devices for the user."""
    user_id_str = payload.get("user_id", "")
    if not user_id_str:
        return
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return
    tokens = [t.token for t in DjangoDeviceTokenRepository().list_by_user(user_id)]
    if not tokens:
        return
    title = _PUSH_TITLES.get(event_name, "Sansaar notification")
    body = _PUSH_BODIES.get(event_name, "")
    count = send_push_multicast(tokens=tokens, title=title, body=body)
    if count:
        logger.info("FCM push sent to %d device(s) for event %s.", count, event_name)


def _handle_event_updated(payload: dict) -> None:
    """Create in-app notifications for all registered attendees when an event is updated.

    The payload must contain event_id and attendee_ids. Each attendee gets an
    in-app notification so they can review the changes and acknowledge.
    """
    from apps.notifications.application.use_cases.batch_create_notifications import (
        BatchCreateNotificationsUseCase,
    )
    from apps.notifications.infrastructure.repositories import (
        DjangoNotificationPreferenceRepository,
        DjangoNotificationRepository,
    )

    event_id = payload.get("event_id", "")
    event_title = payload.get("event_title", "an event")
    attendee_ids_raw = payload.get("attendee_ids", [])

    if not attendee_ids_raw:
        logger.info("event.updated has no attendee_ids, skipping notifications. event_id=%s", event_id)
        return

    try:
        attendee_ids = [uuid.UUID(str(uid)) for uid in attendee_ids_raw]
    except ValueError:
        logger.error("event.updated contained invalid attendee UUID(s). event_id=%s", event_id)
        return

    BatchCreateNotificationsUseCase(
        DjangoNotificationRepository(),
        DjangoNotificationPreferenceRepository(),
    ).execute(
        user_ids=attendee_ids,
        notification_type="event_update",
        channel="in_app",
        title=f"Event updated: {event_title}",
        message="Details for an event you are registered for have changed. Please review the updates.",
        data={"event_id": event_id},
    )
    logger.info(
        "event.updated notifications created for %d attendees. event_id=%s",
        len(attendee_ids),
        event_id,
    )


def _build_mfa_email_otp(payload: dict) -> EmailNotification:
    """Build MFA email OTP delivery message."""
    first_name = payload.get("first_name", "there")
    otp_code = payload.get("otp_code", "")
    html = (
        f"<p>Hi {first_name},</p>"
        f"<p>Your Sansaar verification code is: <strong>{otp_code}</strong></p>"
        "<p>This code expires in 10 minutes. Do not share it with anyone.</p>"
    )
    return EmailNotification(
        to_email=payload.get("email", ""),
        to_name=first_name,
        subject="Your Sansaar verification code",
        html_body=html,
    )


def _build_mfa_sms_otp(payload: dict) -> EmailNotification | None:
    """Build MFA SMS OTP delivery. Uses SMS sender directly, returns None."""
    phone = payload.get("phone", "")
    otp_code = payload.get("otp_code", "")
    if not phone or not otp_code:
        logger.warning("mfa_sms_otp event missing phone or otp_code: %s", payload)
        return None
    # sms delivery handled separately via twilio in the sms sender
    # for now, fall back to email if phone-based sending is not configured
    first_name = payload.get("first_name", "there")
    email = payload.get("email", "")
    if email:
        html = (
            f"<p>Hi {first_name},</p>"
            f"<p>Your Sansaar verification code is: <strong>{otp_code}</strong></p>"
            "<p>This code expires in 10 minutes.</p>"
        )
        return EmailNotification(
            to_email=email,
            to_name=first_name,
            subject="Your Sansaar verification code",
            html_body=html,
        )
    logger.warning("mfa_sms_otp: no email fallback available for phone %s", phone)
    return None


_HANDLERS = {
    "iam.email_verification_requested": _build_email_verification,
    "iam.password_reset_requested": _build_password_reset,
    "iam.password_changed": _build_password_changed,
    "iam.mfa_enabled": _build_mfa_enabled,
    "iam.mfa_disabled": _build_mfa_disabled,
    "iam.account_locked": _build_account_locked,
    "iam.mfa_email_otp_requested": _build_mfa_email_otp,
    "iam.mfa_sms_otp_requested": _build_mfa_sms_otp,
    "participation.registration.created": _build_registration_confirmed,
    "participation.registration.cancelled": _build_registration_cancelled,
    "participation.waitlist.joined": _build_waitlist_joined,
    "participation.waitlist.promoted": _build_waitlist_promoted,
    "org.created": _build_org_created,
    "org.approved": _build_org_approved,
    "org.rejected": _build_org_rejected,
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

        # * event.updated is handled separately - it creates in-app notifications
        if event_name == "event.updated":
            _handle_event_updated(payload)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

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
            logger.debug("Builder returned None for event %s - acking without send.", event_name)

        # fire-and-forget FCM push for participation events
        if event_name.startswith("participation."):
            _send_push_for_participation(event_name, payload)

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
    channel.queue_bind(queue=_QUEUE, exchange=_EXCHANGE, routing_key="org.#")
    channel.queue_bind(queue=_QUEUE, exchange=_EXCHANGE, routing_key="event.#")
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=_QUEUE, on_message_callback=_handle_message)

    logger.info("Notification consumer started. Bound to %s, participation.#, org.#.", _ROUTING_KEY)
    channel.start_consuming()
