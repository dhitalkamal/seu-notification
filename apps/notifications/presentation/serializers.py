"""DRF serializers for notifications request deserialization and response shaping."""

from __future__ import annotations

from rest_framework import serializers


class CreateNotificationSerializer(serializers.Serializer):
    """Payload for creating a notification. user_id targets the recipient."""

    user_id = serializers.UUIDField()
    notification_type = serializers.CharField(max_length=50)
    channel = serializers.ChoiceField(choices=["in_app", "email", "push", "sms"])
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    data = serializers.JSONField(default=dict)


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
    data = serializers.JSONField()
    created_at = serializers.DateTimeField()


class MarkAllReadResponseSerializer(serializers.Serializer):
    """Response shape after marking all notifications as read."""

    count = serializers.IntegerField()
