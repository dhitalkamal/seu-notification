"""Management command that runs the RabbitMQ notification consumer."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.notifications.infrastructure.consumer import start_consuming


class Command(BaseCommand):
    """Long-running process that consumes notification events from RabbitMQ."""

    help = "Start the RabbitMQ notification consumer"

    def handle(self, *args: object, **options: object) -> None:
        """Delegate to the consumer module's blocking start_consuming function."""
        start_consuming()
