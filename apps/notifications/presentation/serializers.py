"""DRF serializers for notifications request deserialization and response shaping."""

from __future__ import annotations

from rest_framework import serializers


class CreateNotificationSerializer(serializers.Serializer):
    """Payload for creating a notification (called internally or by other services)."""

    user_id = serializers.UUIDField()
    notification_type = serializers.CharField(max_length=50)
    channel = serializers.ChoiceField(choices=["in_app", "email", "push", "sms"])
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    data = serializers.DictField(required=False, default=dict)


class NotificationResponseSerializer(serializers.Serializer):
    """Public shape of a notification resource."""

    id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    notification_type = serializers.CharField()
    channel = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    status = serializers.CharField()
    is_read = serializers.BooleanField()
    read_at = serializers.DateTimeField(allow_null=True)
    data = serializers.DictField()
    created_at = serializers.DateTimeField()


class DeviceTokenSerializer(serializers.Serializer):
    """Payload for registering a device push token."""

    token = serializers.CharField(max_length=512)
    platform = serializers.ChoiceField(choices=["ios", "android", "web"])


class DeviceTokenResponseSerializer(serializers.Serializer):
    """Response for a registered device token."""

    id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    token = serializers.CharField()
    platform = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class UpdatePreferenceSerializer(serializers.Serializer):
    """Payload for updating channel preferences for a notification type."""

    email_enabled = serializers.BooleanField()
    push_enabled = serializers.BooleanField()
    sms_enabled = serializers.BooleanField()
    in_app_enabled = serializers.BooleanField()


class NotificationPreferenceResponseSerializer(serializers.Serializer):
    """Public shape of a notification preference resource."""

    id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    notification_type = serializers.CharField()
    email_enabled = serializers.BooleanField()
    push_enabled = serializers.BooleanField()
    sms_enabled = serializers.BooleanField()
    in_app_enabled = serializers.BooleanField()
