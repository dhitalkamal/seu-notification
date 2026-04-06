"""Tests for event.updated consumer handler (item 12)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch


class TestEventUpdatedConsumer:
    """Unit tests for _handle_event_updated in consumer.py."""

    def test_handle_event_updated_creates_notifications(self) -> None:
        """_handle_event_updated must call batch create for all attendee_ids."""
        from apps.notifications.infrastructure.consumer import _handle_event_updated

        event_id = str(uuid.uuid4())
        attendee_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

        with (
            patch("apps.notifications.application.use_cases.batch_create_notifications.BatchCreateNotificationsUseCase") as mock_uc_class,
            patch("apps.notifications.infrastructure.repositories.DjangoNotificationRepository"),
            patch("apps.notifications.infrastructure.repositories.DjangoNotificationPreferenceRepository"),
        ):
            mock_uc = MagicMock()
            mock_uc.execute.return_value = []
            mock_uc_class.return_value = mock_uc

            _handle_event_updated(
                {
                    "event_id": event_id,
                    "event_title": "Test Event",
                    "attendee_ids": attendee_ids,
                }
            )

            mock_uc.execute.assert_called_once()
            call_kwargs = mock_uc.execute.call_args[1]
            assert call_kwargs["notification_type"] == "event_update"
            assert call_kwargs["channel"] == "in_app"
            assert len(call_kwargs["user_ids"]) == 2

    def test_handle_event_updated_skips_when_no_attendees(self) -> None:
        """_handle_event_updated must not call batch create when attendee_ids is empty."""
        from apps.notifications.infrastructure.consumer import _handle_event_updated

        with patch("apps.notifications.application.use_cases.batch_create_notifications.BatchCreateNotificationsUseCase") as mock_uc_class:
            _handle_event_updated({"event_id": str(uuid.uuid4()), "attendee_ids": []})
            mock_uc_class.assert_not_called()

    def test_handle_event_updated_logs_error_for_invalid_uuid(self) -> None:
        """_handle_event_updated must not raise on malformed attendee UUIDs."""
        from apps.notifications.infrastructure.consumer import _handle_event_updated

        # should not raise - just log and return
        _handle_event_updated(
            {
                "event_id": str(uuid.uuid4()),
                "attendee_ids": ["not-a-uuid"],
            }
        )
