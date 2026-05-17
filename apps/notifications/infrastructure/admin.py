"""Django admin registrations for notifications domain models."""

from __future__ import annotations

from django.contrib import admin

from apps.notifications.infrastructure.models import Notification, NotificationPreference

admin.site.register(Notification)
admin.site.register(NotificationPreference)
