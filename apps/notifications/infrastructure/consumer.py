"""RabbitMQ consumer for incoming IAM notification events."""

from __future__ import annotations

import json
import logging

import pika
from django.conf import settings

from apps.notifications.application.use_cases.send_email import SendEmailUseCase
from apps.notifications.domain.entities import EmailNotification
from apps.notifications.infrastructure.senders.gmail_sender import GmailEmailSender
from apps.notifications.infrastructure.senders.sendgrid_sender import SendGridEmailSender

logger = logging.getLogger(__name__)

_EXCHANGE = "sansaar"
_EXCHANGE_TYPE = "topic"
_QUEUE = "notifications.iam"
_ROUTING_KEY = "iam.*"
_API_QUEUE = "notifications.api"
_API_ROUTING_KEY = "notification.api"


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


def _build_api_notification(payload: dict) -> EmailNotification:
    """Build an email from a generic API-triggered notification payload."""
    return EmailNotification(
        to_email=payload.get("to_email", ""),
        to_name=payload.get("to_name", ""),
        subject=payload.get("subject", "Notification"),
        html_body=payload.get("html_body", ""),
    )


_HANDLERS = {
    "iam.email_verification_requested": _build_email_verification,
    "iam.password_reset_requested": _build_password_reset,
    "notification.api": _build_api_notification,
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
        SendEmailUseCase(SendGridEmailSender(), GmailEmailSender()).execute(notification)

        if event_name == "notification.api" and payload.get("notification_id"):
            import uuid as _uuid

            from apps.notifications.infrastructure.repositories import DjangoNotificationRepository

            DjangoNotificationRepository().update_status(
                _uuid.UUID(payload["notification_id"]), "delivered"
            )

        channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(
            "Email sent for event %s to %s.",
            event_name,
            payload.get("to_email", payload.get("email")),
        )
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
    channel.queue_bind(queue=_QUEUE, exchange=_EXCHANGE, routing_key=_ROUTING_KEY)

    channel.queue_declare(queue=_API_QUEUE, durable=True)
    channel.queue_bind(queue=_API_QUEUE, exchange=_EXCHANGE, routing_key=_API_ROUTING_KEY)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=_QUEUE, on_message_callback=_handle_message)
    channel.basic_consume(queue=_API_QUEUE, on_message_callback=_handle_message)

    logger.info(
        "Notification consumer started. Waiting for messages on %s and %s.",
        _QUEUE,
        _API_QUEUE,
    )
    channel.start_consuming()
