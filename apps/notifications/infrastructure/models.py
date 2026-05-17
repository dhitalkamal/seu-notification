"""Django ORM models for the notifications domain. Maps to the notifications schema."""

from __future__ import annotations

import uuid

from django.db import models

from apps.notifications.domain.entities import NotificationEntity, NotificationPreferenceEntity


class Notification(models.Model):
    """A single notification record for a platform user."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-App"
        EMAIL = "email", "Email"
        PUSH = "push", "Push"
        SMS = "sms", "SMS"

    class Meta:
        db_table = '"notifications"."notification"'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    notification_type = models.CharField(max_length=50)
    channel = models.CharField(max_length=20, choices=Channel.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def to_entity(self) -> NotificationEntity:
        """Map this ORM row to a pure-Python NotificationEntity."""
        return NotificationEntity(
            id=self.id,
            user_id=self.user_id,
            notification_type=self.notification_type,
            channel=self.channel,
            title=self.title,
            message=self.message,
            status=self.status,
            is_read=self.is_read,
            created_at=self.created_at,
            data=self.data,
            read_at=self.read_at,
        )

    @classmethod
    def from_entity(cls, entity: NotificationEntity) -> "Notification":
        """Build an unsaved ORM instance from a NotificationEntity."""
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            notification_type=entity.notification_type,
            channel=entity.channel,
            title=entity.title,
            message=entity.message,
            status=entity.status,
            is_read=entity.is_read,
            data=entity.data,
            read_at=entity.read_at,
        )


class NotificationPreference(models.Model):
    """Per-user, per-type channel preferences."""

    class Meta:
        db_table = '"notifications"."notification_preference"'
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "notification_type"],
                name="unique_user_notification_type",
            )
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    notification_type = models.CharField(max_length=50)
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    in_app_enabled = models.BooleanField(default=True)

    def to_entity(self) -> NotificationPreferenceEntity:
        """Map this ORM row to a pure-Python NotificationPreferenceEntity."""
        return NotificationPreferenceEntity(
            id=self.id,
            user_id=self.user_id,
            notification_type=self.notification_type,
            email_enabled=self.email_enabled,
            push_enabled=self.push_enabled,
            sms_enabled=self.sms_enabled,
            in_app_enabled=self.in_app_enabled,
        )
