"""Django ORM model for event update acknowledgements."""

from __future__ import annotations

import uuid

from django.db import models


class EventUpdateAcknowledgement(models.Model):
    """Records that a specific user acknowledged an event-update notification.

    One record per (notification_id, user_id) pair - repeated calls are idempotent
    via get_or_create on those two fields.
    """

    class Meta:
        db_table = "notifications_event_update_acknowledgement"
        constraints = [
            models.UniqueConstraint(
                fields=["notification_id", "user_id"],
                name="unique_event_update_ack",
            )
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification_id = models.UUIDField()
    user_id = models.UUIDField()
    event_id = models.UUIDField()
    acknowledged_at = models.DateTimeField(auto_now_add=True)
