"""Django ORM model for audit digest schedule configuration."""

from __future__ import annotations

import uuid

from django.db import models


class AuditDigestSchedule(models.Model):
    """Stores configuration for scheduled audit digest emails."""

    class Frequency(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    class Meta:
        db_table = '"notifications"."audit_digest_schedule"'
        ordering = ["-created_at"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    frequency = models.CharField(max_length=20, choices=Frequency.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.UUIDField()

    def __str__(self) -> str:
        """Return a readable label for admin and debugging."""
        return f"{self.email} ({self.frequency})"
