"""RabbitMQ publisher for notification email delivery jobs."""

from __future__ import annotations

import json
import uuid

import pika
from django.conf import settings

from apps.notifications.domain.repositories import IPublisher

_EXCHANGE = "sansaar"
_EXCHANGE_TYPE = "topic"
_ROUTING_KEY = "notification.api"


class RabbitMQPublisher(IPublisher):
    """Publishes email delivery jobs to the sansaar topic exchange."""

    def publish(
        self,
        *,
        notification_id: uuid.UUID,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
    ) -> None:
        """Serialise the payload and publish to the sansaar exchange."""
        payload = json.dumps(
            {
                "notification_id": str(notification_id),
                "to_email": to_email,
                "to_name": to_name,
                "subject": subject,
                "html_body": html_body,
            }
        ).encode()

        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()
        channel.exchange_declare(exchange=_EXCHANGE, exchange_type=_EXCHANGE_TYPE, durable=True)
        channel.basic_publish(
            exchange=_EXCHANGE,
            routing_key=_ROUTING_KEY,
            body=payload,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
