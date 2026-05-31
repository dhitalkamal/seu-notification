"""DRF serializers for the audit digest schedule API."""

from __future__ import annotations

from rest_framework import serializers


class AuditDigestScheduleCreateSerializer(serializers.Serializer):
    """Payload for creating a new digest schedule."""

    email = serializers.EmailField()
    frequency = serializers.ChoiceField(choices=["daily", "weekly", "monthly"])


class AuditDigestSchedulePatchSerializer(serializers.Serializer):
    """Payload for updating an existing digest schedule (all fields optional)."""

    frequency = serializers.ChoiceField(choices=["daily", "weekly", "monthly"], required=False)
    is_active = serializers.BooleanField(required=False)


class AuditDigestScheduleResponseSerializer(serializers.Serializer):
    """Public shape of an audit digest schedule resource."""

    id = serializers.UUIDField()
    email = serializers.EmailField()
    frequency = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    created_by = serializers.UUIDField()
