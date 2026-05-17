"""URL routes for the notifications app."""

from __future__ import annotations

from django.urls import URLPattern, path

from .views import (
    DeviceTokenView,
    HealthCheckView,
    NotificationListCreateView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationPreferenceView,
)

urlpatterns: list[URLPattern] = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("notifications/", NotificationListCreateView.as_view(), name="notification-list-create"),
    path(
        "notifications/<uuid:notification_id>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
    path(
        "notifications/mark-all-read/",
        NotificationMarkAllReadView.as_view(),
        name="notification-mark-all-read",
    ),
    path("device-tokens/", DeviceTokenView.as_view(), name="device-token-register"),
    path(
        "preferences/<str:notification_type>/",
        NotificationPreferenceView.as_view(),
        name="notification-preference",
    ),
]
