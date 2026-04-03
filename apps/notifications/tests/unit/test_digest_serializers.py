"""Unit tests for AuditDigestSchedule model and digest schedule API views."""

from __future__ import annotations

import uuid

# mark all tests in this file to use django db if needed
# these are pure unit tests against serializer logic and fake data


def test_digest_schedule_create_valid_payload():
    """A schedule with email, frequency, and created_by is valid."""
    from apps.notifications.presentation.digest_serializers import (
        AuditDigestScheduleCreateSerializer,
    )

    created_by = uuid.uuid4()
    ser = AuditDigestScheduleCreateSerializer(
        data={
            "email": "admin@example.com",
            "frequency": "weekly",
            "created_by": str(created_by),
        }
    )
    assert ser.is_valid(), ser.errors
    assert ser.validated_data["email"] == "admin@example.com"
    assert ser.validated_data["frequency"] == "weekly"


def test_digest_schedule_invalid_frequency():
    """An unknown frequency value fails validation."""
    from apps.notifications.presentation.digest_serializers import (
        AuditDigestScheduleCreateSerializer,
    )

    ser = AuditDigestScheduleCreateSerializer(
        data={
            "email": "admin@example.com",
            "frequency": "hourly",
            "created_by": str(uuid.uuid4()),
        }
    )
    assert not ser.is_valid()
    assert "frequency" in ser.errors


def test_digest_schedule_missing_email():
    """Missing email field fails validation."""
    from apps.notifications.presentation.digest_serializers import (
        AuditDigestScheduleCreateSerializer,
    )

    ser = AuditDigestScheduleCreateSerializer(
        data={
            "frequency": "daily",
            "created_by": str(uuid.uuid4()),
        }
    )
    assert not ser.is_valid()
    assert "email" in ser.errors


def test_digest_schedule_patch_serializer_is_active():
    """Patch serializer accepts is_active toggle."""
    from apps.notifications.presentation.digest_serializers import (
        AuditDigestSchedulePatchSerializer,
    )

    ser = AuditDigestSchedulePatchSerializer(data={"is_active": False})
    assert ser.is_valid(), ser.errors
    assert ser.validated_data["is_active"] is False


def test_digest_schedule_patch_serializer_frequency():
    """Patch serializer accepts frequency change."""
    from apps.notifications.presentation.digest_serializers import (
        AuditDigestSchedulePatchSerializer,
    )

    ser = AuditDigestSchedulePatchSerializer(data={"frequency": "monthly"})
    assert ser.is_valid(), ser.errors
    assert ser.validated_data["frequency"] == "monthly"


def test_digest_schedule_response_serializer_shape():
    """Response serializer produces expected fields."""
    from apps.notifications.presentation.digest_serializers import (
        AuditDigestScheduleResponseSerializer,
    )

    data = {
        "id": str(uuid.uuid4()),
        "email": "admin@example.com",
        "frequency": "daily",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00Z",
        "created_by": str(uuid.uuid4()),
    }
    ser = AuditDigestScheduleResponseSerializer(data=data)
    assert ser.is_valid(), ser.errors
    assert "email" in ser.validated_data
    assert "frequency" in ser.validated_data
    assert "is_active" in ser.validated_data
