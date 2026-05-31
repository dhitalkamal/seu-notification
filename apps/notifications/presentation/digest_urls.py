"""URL routes for the audit digest schedule endpoints."""

from __future__ import annotations

from django.urls import URLPattern, path

from .digest_views import DigestScheduleDetailView, DigestScheduleListCreateView

urlpatterns: list[URLPattern] = [
    path("", DigestScheduleListCreateView.as_view(), name="digest-schedule-list-create"),
    path("<uuid:schedule_id>/", DigestScheduleDetailView.as_view(), name="digest-schedule-detail"),
]
