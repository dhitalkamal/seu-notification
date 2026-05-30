"""Add audit_digest_schedule table to the notifications schema."""

from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    """Creates the AuditDigestSchedule table."""

    dependencies = [
        ("notifications", "0002_add_event_journey_stages"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditDigestSchedule",
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
                ("email", models.EmailField()),
                (
                    "frequency",
                    models.CharField(
                        choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.UUIDField()),
            ],
            options={
                "db_table": "notifications_audit_digest_schedule",
                "ordering": ["-created_at"],
            },
        ),
    ]
