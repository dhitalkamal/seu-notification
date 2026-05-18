"""URL routes for the notifications app."""

from __future__ import annotations

from django.urls import URLPattern, path

from .views import (
    BatchNotificationView,
    DeviceTokenView,
    EventJourneyView,
    HealthCheckView,
    NotificationListCreateView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationPreferenceView,
    NotificationUnreadCountView,
)

urlpatterns: list[URLPattern] = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("notifications/", NotificationListCreateView.as_view(), name="notification-list-create"),
    path(
        "notifications/batch/",
        BatchNotificationView.as_view(),
        name="notification-batch-create",
    ),
    path(
        "notifications/unread-count/",
        NotificationUnreadCountView.as_view(),
        name="notification-unread-count",
    ),
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
    path(
        "journeys/events/<uuid:event_id>/",
        EventJourneyView.as_view(),
        name="event-journey",
    ),
]
