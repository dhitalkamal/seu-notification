"""Migration: add event_update_acknowledgement table."""

from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    """Creates the EventUpdateAcknowledgement table in the notifications schema."""

    dependencies = [
        ("notifications", "0003_add_audit_digest_schedule"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventUpdateAcknowledgement",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("notification_id", models.UUIDField()),
                ("user_id", models.UUIDField()),
                ("event_id", models.UUIDField()),
                ("acknowledged_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": '"notifications"."event_update_acknowledgement"',
            },
        ),
        migrations.AddConstraint(
            model_name="eventupdateacknowledgement",
            constraint=models.UniqueConstraint(
                fields=["notification_id", "user_id"],
                name="unique_event_update_ack",
            ),
        ),
    ]
