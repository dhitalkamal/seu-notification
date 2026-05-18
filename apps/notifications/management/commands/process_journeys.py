"""Management command: fire due journey notification stages."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from apps.notifications.application.use_cases.get_due_stages import GetDueStagesUseCase
from apps.notifications.infrastructure.repositories import DjangoEventJourneyRepository

logger = logging.getLogger(__name__)

_STAGE_MESSAGES = {
    "pre_event_week": ("Event in 1 week!", "Your event starts in 7 days. Get ready!"),
    "pre_event_day": ("Event tomorrow!", "Reminder: your event is tomorrow."),
    "pre_event_hour": ("Event in 1 hour!", "Your event starts in 1 hour. See you there!"),
    "post_event_followup": ("Thanks for attending!", "Hope you enjoyed the event. Share feedback!"),
    "certificate_ready": (
        "Your certificate is ready!",
        "Your participation certificate is now available in My Tickets.",
    ),
}


class Command(BaseCommand):
    """Process and fire pending event journey stages whose trigger_at has passed."""

    help = "Fire due Intelligent Event Journey notification stages."

    def handle(self, *args: object, **options: object) -> None:
        """Query due stages, publish notifications, and mark them fired."""
        repo = DjangoEventJourneyRepository()
        now = datetime.now(timezone.utc)
        due = GetDueStagesUseCase(repo).execute(as_of=now)

        fired = 0
        for stage in due:
            try:
                title, body = _STAGE_MESSAGES.get(
                    stage.stage_type,
                    ("Event update", "You have an upcoming event."),
                )
                # publish to RabbitMQ for push/email delivery
                self._publish(stage.event_id, stage.stage_type, title, body)
                repo.mark_stage_fired(stage.id)
                fired += 1
                logger.info(
                    "Journey stage fired: event=%s type=%s",
                    stage.event_id,
                    stage.stage_type,
                )
            except Exception:
                logger.exception("Failed to fire journey stage %s (%s)", stage.id, stage.stage_type)

        self.stdout.write(f"Fired {fired} journey stage(s).")

    def _publish(
        self,
        event_id: object,
        stage_type: str,
        title: str,
        body: str,
    ) -> None:
        """Publish the journey stage notification via RabbitMQ."""
        import json
        import os

        import pika

        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        params = pika.URLParameters(rabbitmq_url)
        try:
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.exchange_declare(exchange="sansaar", exchange_type="topic", durable=True)
            ch.basic_publish(
                exchange="sansaar",
                routing_key=f"journey.{stage_type}",
                body=json.dumps(
                    {
                        "event_id": str(event_id),
                        "stage_type": stage_type,
                        "title": title,
                        "body": body,
                    }
                ).encode(),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            conn.close()
        except Exception:
            logger.warning("RabbitMQ unavailable - journey notification not published.")
