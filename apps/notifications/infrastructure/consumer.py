"""RabbitMQ consumer for incoming notification events."""

from __future__ import annotations

import json
import logging

import pika
import pika.exceptions
from django.conf import settings

from apps.notifications.application.use_cases.send_email import SendEmailUseCase
from apps.notifications.domain.entities import EmailNotification
from apps.notifications.infrastructure.senders.gmail_sender import GmailEmailSender
from apps.notifications.infrastructure.senders.sendgrid_sender import SendGridEmailSender

logger = logging.getLogger(__name__)

_EXCHANGE = "sansaar"
_EXCHANGE_TYPE = "topic"
_QUEUE = "notifications.email_verification"
_ROUTING_KEY = "iam.email_verification_requested"


def _build_otp_email(payload: dict) -> EmailNotification:
    """Build the verification email from a raw event payload dict."""
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


def _handle_message(
    channel: pika.channel.Channel, method: pika.spec.Basic.Deliver, _props: object, body: bytes
) -> None:
    """Process a single message from the queue."""
    try:
        payload = json.loads(body)
        notification = _build_otp_email(payload)
        use_case = SendEmailUseCase(SendGridEmailSender(), GmailEmailSender())
        use_case.execute(notification)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("Verification email sent to %s.", payload.get("email"))
    except Exception:
        logger.error("Failed to process notification message.", exc_info=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consuming() -> None:
    """Connect to RabbitMQ, declare the topology, and block on message consumption."""
    params = pika.URLParameters(settings.RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange=_EXCHANGE, exchange_type=_EXCHANGE_TYPE, durable=True)
    channel.queue_declare(queue=_QUEUE, durable=True)
    channel.queue_bind(queue=_QUEUE, exchange=_EXCHANGE, routing_key=_ROUTING_KEY)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=_QUEUE, on_message_callback=_handle_message)

    logger.info("Notification consumer started. Waiting for messages on %s.", _QUEUE)
    channel.start_consuming()
