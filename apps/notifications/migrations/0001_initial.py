"""Create notifications and notification_preferences tables."""

from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    """Initial notifications tables."""

    dependencies = [
        ("notifications", "0000_create_notifications_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("user_id", models.UUIDField()),
                ("notification_type", models.CharField(max_length=50)),
                (
                    "channel",
                    models.CharField(
                        choices=[
                            ("in_app", "In-App"),
                            ("email", "Email"),
                            ("push", "Push"),
                            ("sms", "SMS"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("delivered", "Delivered"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("is_read", models.BooleanField(default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("data", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": '"notifications"."notification"'},
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("user_id", models.UUIDField()),
                ("notification_type", models.CharField(max_length=50)),
                ("email_enabled", models.BooleanField(default=True)),
                ("push_enabled", models.BooleanField(default=True)),
                ("sms_enabled", models.BooleanField(default=False)),
                ("in_app_enabled", models.BooleanField(default=True)),
            ],
            options={"db_table": '"notifications"."notification_preference"'},
        ),
        migrations.AddConstraint(
            model_name="notificationpreference",
            constraint=models.UniqueConstraint(
                fields=["user_id", "notification_type"],
                name="unique_user_notification_type",
            ),
        ),
    ]
