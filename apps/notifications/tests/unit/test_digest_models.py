"""Unit tests for AuditDigestSchedule model field defaults and choices."""

from __future__ import annotations

import uuid


def test_frequency_choices_are_correct():
    """Frequency choices cover daily, weekly, and monthly only."""
    from apps.notifications.infrastructure.digest_models import AuditDigestSchedule

    choices = [c[0] for c in AuditDigestSchedule.Frequency.choices]
    assert set(choices) == {"daily", "weekly", "monthly"}


def test_model_meta_db_table():
    """Model uses the notifications schema and correct table name."""
    from apps.notifications.infrastructure.digest_models import AuditDigestSchedule

    assert AuditDigestSchedule._meta.db_table == '"notifications"."audit_digest_schedule"'


def test_model_default_is_active_true():
    """is_active defaults to True without explicit value."""
    from apps.notifications.infrastructure.digest_models import AuditDigestSchedule

    # use uuid and check field default value - no db access
    field = AuditDigestSchedule._meta.get_field("is_active")
    assert field.default is True


def test_model_id_is_uuid():
    """Primary key is a UUID field."""
    from apps.notifications.infrastructure.digest_models import AuditDigestSchedule

    field = AuditDigestSchedule._meta.get_field("id")
    assert field.primary_key is True
    assert field.default is uuid.uuid4
