"""Tests for EventUpdateAcknowledgement model and endpoints (item 12)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from apps.notifications.infrastructure.acknowledgement_models import EventUpdateAcknowledgement


class TestEventUpdateAcknowledgementModel:
    """Model-level tests for EventUpdateAcknowledgement."""

    def test_model_has_expected_fields(self) -> None:
        """Model must expose notification_id, user_id, event_id, acknowledged_at."""
        assert hasattr(EventUpdateAcknowledgement, "notification_id")
        assert hasattr(EventUpdateAcknowledgement, "user_id")
        assert hasattr(EventUpdateAcknowledgement, "event_id")
        assert hasattr(EventUpdateAcknowledgement, "acknowledged_at")

    def test_model_meta_table_name(self) -> None:
        """Model must use the notifications schema."""
        assert EventUpdateAcknowledgement._meta.db_table == "notifications_event_update_acknowledgement"


class TestAcknowledgeEndpointLogic:
    """Unit tests for the acknowledge and list endpoints."""

    def _make_request(self, method: str, path: str, data: dict | None = None) -> object:
        """Build an authenticated DRF request."""
        from rest_framework.parsers import JSONParser
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        if method == "post":
            django_request = factory.post(path, data=data or {}, format="json")
        else:
            django_request = factory.get(path)

        request = Request(django_request, parsers=[JSONParser()])
        fake_user = MagicMock()
        fake_user.id = str(uuid.uuid4())
        fake_user.is_authenticated = True
        request._user = fake_user
        return request

    def test_acknowledge_creates_record_and_returns_201(self) -> None:
        """POST /notifications/{id}/acknowledge/ must return 201."""
        from apps.notifications.presentation.views import AcknowledgeNotificationView

        notification_id = uuid.uuid4()
        event_id = uuid.uuid4()
        request = self._make_request("post", f"/api/v1/notifications/{notification_id}/acknowledge/", {"event_id": str(event_id)})

        with patch("apps.notifications.presentation.views.EventUpdateAcknowledgement") as mock_model:
            mock_instance = MagicMock()
            mock_instance.id = uuid.uuid4()
            mock_instance.acknowledged_at = MagicMock()
            mock_instance.acknowledged_at.isoformat.return_value = "2026-01-01T00:00:00Z"
            mock_model.objects.get_or_create.return_value = (mock_instance, True)

            view = AcknowledgeNotificationView()
            view.permission_classes = []
            view.authentication_classes = []
            view.kwargs = {}
            view.args = ()
            view.request = request
            view.format_kwarg = None
            view.headers = {}

            response = view.post(request, notification_id=notification_id)

        assert response.status_code == 201

    def test_acknowledge_already_acked_returns_200(self) -> None:
        """POST again on already-acknowledged notification must return 200."""
        from apps.notifications.presentation.views import AcknowledgeNotificationView

        notification_id = uuid.uuid4()
        event_id = uuid.uuid4()
        request = self._make_request("post", f"/api/v1/notifications/{notification_id}/acknowledge/", {"event_id": str(event_id)})

        with patch("apps.notifications.presentation.views.EventUpdateAcknowledgement") as mock_model:
            mock_instance = MagicMock()
            mock_instance.id = uuid.uuid4()
            mock_instance.acknowledged_at = MagicMock()
            mock_instance.acknowledged_at.isoformat.return_value = "2026-01-01T00:00:00Z"
            # created=False means it already existed
            mock_model.objects.get_or_create.return_value = (mock_instance, False)

            view = AcknowledgeNotificationView()
            view.permission_classes = []
            view.authentication_classes = []
            view.kwargs = {}
            view.args = ()
            view.request = request
            view.format_kwarg = None
            view.headers = {}

            response = view.post(request, notification_id=notification_id)

        assert response.status_code == 200

    def test_list_acknowledgements_returns_200(self) -> None:
        """GET /notifications/event/{event_id}/acknowledgements/ must return 200."""
        from apps.notifications.presentation.views import EventAcknowledgementsListView

        event_id = uuid.uuid4()
        request = self._make_request("get", f"/api/v1/notifications/event/{event_id}/acknowledgements/")

        with patch("apps.notifications.presentation.views.EventUpdateAcknowledgement") as mock_model:
            mock_model.objects.filter.return_value.values.return_value = []

            view = EventAcknowledgementsListView()
            view.permission_classes = []
            view.authentication_classes = []
            view.kwargs = {}
            view.args = ()
            view.request = request
            view.format_kwarg = None
            view.headers = {}

            response = view.get(request, event_id=event_id)

        assert response.status_code == 200

    def test_acknowledge_missing_event_id_raises_validation_error(self) -> None:
        """POST without event_id must raise DRF ValidationError (400)."""
        from rest_framework.exceptions import ValidationError

        from apps.notifications.presentation.views import AcknowledgeNotificationView

        notification_id = uuid.uuid4()
        request = self._make_request("post", f"/api/v1/notifications/{notification_id}/acknowledge/", {})

        view = AcknowledgeNotificationView()
        view.permission_classes = []
        view.authentication_classes = []
        view.kwargs = {}
        view.args = ()
        view.request = request
        view.format_kwarg = None
        view.headers = {}

        with pytest.raises(ValidationError):
            view.post(request, notification_id=notification_id)
