"""URL routes for the notifications app."""

from __future__ import annotations

from django.urls import URLPattern, path

from .views import (
    HealthCheckView,
    MarkAllReadView,
    MarkNotificationReadView,
    NotificationListCreateView,
)

urlpatterns: list[URLPattern] = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("notifications/mark-all-read/", MarkAllReadView.as_view(), name="mark-all-read"),
    path("notifications/", NotificationListCreateView.as_view(), name="notification-list-create"),
    path(
        "notifications/<uuid:notification_id>/read/",
        MarkNotificationReadView.as_view(),
        name="mark-read",
    ),
]
