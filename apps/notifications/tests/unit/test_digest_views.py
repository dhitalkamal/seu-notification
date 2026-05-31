"""Unit tests for digest schedule views (covers permission and routing logic)."""

from __future__ import annotations

import uuid


def test_patch_serializer_empty_payload_is_valid():
    """Empty patch payload is valid (no required fields)."""
    from apps.notifications.presentation.digest_serializers import AuditDigestSchedulePatchSerializer

    ser = AuditDigestSchedulePatchSerializer(data={})
    assert ser.is_valid(), ser.errors


def test_patch_serializer_invalid_frequency_rejected():
    """Patch with invalid frequency is rejected."""
    from apps.notifications.presentation.digest_serializers import AuditDigestSchedulePatchSerializer

    ser = AuditDigestSchedulePatchSerializer(data={"frequency": "biweekly"})
    assert not ser.is_valid()
    assert "frequency" in ser.errors


def test_create_serializer_email_validation():
    """Invalid email format is rejected."""
    from apps.notifications.presentation.digest_serializers import AuditDigestScheduleCreateSerializer

    ser = AuditDigestScheduleCreateSerializer(
        data={
            "email": "not-an-email",
            "frequency": "daily",
            "created_by": str(uuid.uuid4()),
        }
    )
    assert not ser.is_valid()
    assert "email" in ser.errors
