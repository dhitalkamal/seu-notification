"""DRF API views for notifications endpoints."""

from __future__ import annotations

import uuid

from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.api.responses import created_response, error_response, success_response
from apps.common.health import check_database, check_rabbitmq, check_redis
from apps.notifications.application.use_cases.batch_create_notifications import (
    BatchCreateNotificationsUseCase,
)
from apps.notifications.application.use_cases.create_journey import CreateEventJourneyUseCase
from apps.notifications.application.use_cases.create_notification import CreateNotificationUseCase
from apps.notifications.application.use_cases.get_due_stages import GetDueStagesUseCase
from apps.notifications.application.use_cases.mark_all_read import MarkAllReadUseCase
from apps.notifications.application.use_cases.mark_notification_read import (
    MarkNotificationReadUseCase,
)
from apps.notifications.application.use_cases.register_device_token import (
    RegisterDeviceTokenUseCase,
)
from apps.notifications.application.use_cases.update_preference import (
    UpdateNotificationPreferenceUseCase,
)
from apps.notifications.infrastructure.repositories import (
    DjangoDeviceTokenRepository,
    DjangoEventJourneyRepository,
    DjangoNotificationPreferenceRepository,
    DjangoNotificationRepository,
)
from apps.notifications.presentation.serializers import (
    CreateNotificationSerializer,
    DeviceTokenResponseSerializer,
    DeviceTokenSerializer,
    NotificationPreferenceResponseSerializer,
    NotificationResponseSerializer,
    UpdatePreferenceSerializer,
)

_NOTIF_REPO = DjangoNotificationRepository
_PREF_REPO = DjangoNotificationPreferenceRepository
_TOKEN_REPO = DjangoDeviceTokenRepository
_JOURNEY_REPO = DjangoEventJourneyRepository
_CREATE_UC = CreateNotificationUseCase
_BATCH_CREATE_UC = BatchCreateNotificationsUseCase
_MARK_READ_UC = MarkNotificationReadUseCase
_MARK_ALL_UC = MarkAllReadUseCase
_REGISTER_TOKEN_UC = RegisterDeviceTokenUseCase
_UPDATE_PREF_UC = UpdateNotificationPreferenceUseCase
_CREATE_JOURNEY_UC = CreateEventJourneyUseCase
_GET_DUE_STAGES_UC = GetDueStagesUseCase
_NOTIF_RESP = NotificationResponseSerializer
_PREF_RESP = NotificationPreferenceResponseSerializer
_TOKEN_RESP = DeviceTokenResponseSerializer

_CHECKS = inline_serializer(
    name="DependencyChecks",
    fields={
        "database": serializers.ChoiceField(choices=["healthy", "unhealthy"]),
        "redis": serializers.ChoiceField(choices=["healthy", "unhealthy"]),
        "rabbitmq": serializers.ChoiceField(choices=["healthy", "unhealthy"]),
    },
)
_META_SCHEMA = inline_serializer(
    name="ResponseMeta",
    fields={
        "request_id": serializers.CharField(),
        "timestamp": serializers.CharField(),
    },
)


class HealthCheckView(APIView):
    """Reports the operational status of all external dependencies."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Health"],
        summary="Service health check",
        description=(
            "Checks connectivity to PostgreSQL, Redis, and RabbitMQ. "
            "Returns 200 when all dependencies are healthy, 503 when any are down."
        ),
        auth=[],
        responses={
            200: OpenApiResponse(
                description="All dependencies are healthy.",
                response=inline_serializer(
                    name="HealthyResponse",
                    fields={
                        "data": inline_serializer(
                            name="HealthyData",
                            fields={
                                "service": serializers.CharField(),
                                "status": serializers.CharField(),
                                "version": serializers.CharField(),
                                "checks": _CHECKS,
                            },
                        ),
                        "error": serializers.JSONField(allow_null=True),
                        "meta": _META_SCHEMA,
                    },
                ),
            ),
            503: OpenApiResponse(
                description="One or more dependencies are unavailable.",
                response=inline_serializer(
                    name="UnhealthyResponse",
                    fields={
                        "data": serializers.JSONField(allow_null=True),
                        "error": inline_serializer(
                            name="HealthError",
                            fields={
                                "code": serializers.CharField(),
                                "message": serializers.CharField(),
                                "details": serializers.JSONField(allow_null=True),
                            },
                        ),
                        "meta": _META_SCHEMA,
                    },
                ),
            ),
        },
    )
    def get(self, request: Request) -> Response:
        """Check DB, Redis, and RabbitMQ and return an aggregated status."""
        db_status, db_err = check_database()
        redis_status, redis_err = check_redis()
        rmq_status, rmq_err = check_rabbitmq()

        checks: dict = {
            "database": db_status,
            "redis": redis_status,
            "rabbitmq": rmq_status,
        }
        dep_errors: dict = {
            k: v
            for k, v in {
                "database": db_err,
                "redis": redis_err,
                "rabbitmq": rmq_err,
            }.items()
            if v is not None
        }

        all_healthy = all(s == "healthy" for s in checks.values())

        if all_healthy:
            return success_response(
                {
                    "service": settings.SERVICE_NAME,
                    "status": "healthy",
                    "version": "0.1.0",
                    "checks": checks,
                },
                request=request,
            )

        return error_response(
            code="ERR_SERVICE_UNHEALTHY",
            message="One or more dependencies are unavailable.",
            details={"checks": checks, **({"errors": dep_errors} if dep_errors else {})},
            http_status=503,
            request=request,
        )


class NotificationListCreateView(APIView):
    """List own notifications (GET) or create a notification (POST)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="List my notifications",
        description="Returns all notifications for the authenticated user, newest first.",
        responses={
            200: OpenApiResponse(description="Notifications.", response=_NOTIF_RESP(many=True)),
            401: OpenApiResponse(description="Missing or invalid JWT."),
        },
    )
    def get(self, request: Request) -> Response:
        """Return all notifications for the authenticated user."""
        results = _NOTIF_REPO().list_by_user(uuid.UUID(str(request.user.id)))
        return success_response(_NOTIF_RESP(results, many=True).data, request=request)

    @extend_schema(
        tags=["Notifications"],
        summary="Create a notification",
        description="Creates a notification for a user. Called by other services or admin.",
        request=CreateNotificationSerializer,
        responses={
            201: OpenApiResponse(description="Notification created.", response=_NOTIF_RESP),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def post(self, request: Request) -> Response:
        """Validate payload and create the notification."""
        ser = CreateNotificationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        entity = _CREATE_UC(_NOTIF_REPO(), _PREF_REPO()).execute(
            user_id=d["user_id"],
            notification_type=d["notification_type"],
            channel=d["channel"],
            title=d["title"],
            message=d["message"],
            data=d.get("data", {}),
        )
        return created_response(_NOTIF_RESP(entity).data, request=request)


class NotificationMarkReadView(APIView):
    """Mark a single notification as read."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="Mark notification as read",
        request=None,
        responses={
            200: OpenApiResponse(description="Notification marked read.", response=_NOTIF_RESP),
            401: OpenApiResponse(description="Missing or invalid JWT."),
            404: OpenApiResponse(description="Notification not found."),
        },
    )
    def post(self, request: Request, notification_id: uuid.UUID) -> Response:
        """Mark the notification as read."""
        entity = _MARK_READ_UC(_NOTIF_REPO()).execute(
            notification_id=notification_id,
            user_id=uuid.UUID(str(request.user.id)),
        )
        return success_response(_NOTIF_RESP(entity).data, request=request)


class NotificationMarkAllReadView(APIView):
    """Mark all of the authenticated user's notifications as read."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="Mark all notifications as read",
        request=None,
        responses={
            200: OpenApiResponse(description="All notifications marked read."),
            401: OpenApiResponse(description="Missing or invalid JWT."),
        },
    )
    def post(self, request: Request) -> Response:
        """Mark all unread notifications as read and return count."""
        count = _MARK_ALL_UC(_NOTIF_REPO()).execute(
            user_id=uuid.UUID(str(request.user.id)),
        )
        return success_response({"updated": count}, request=request)


class DeviceTokenView(APIView):
    """Register a push notification device token."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Device Tokens"],
        summary="Register device token",
        request=DeviceTokenSerializer,
        responses={
            201: OpenApiResponse(description="Token registered.", response=_TOKEN_RESP),
            401: OpenApiResponse(description="Missing or invalid JWT."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def post(self, request: Request) -> Response:
        """Register or reactivate a device push token."""
        ser = DeviceTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        entity = _REGISTER_TOKEN_UC(_TOKEN_REPO()).execute(
            user_id=uuid.UUID(str(request.user.id)),
            token=d["token"],
            platform=d["platform"],
        )
        return created_response(_TOKEN_RESP(entity).data, request=request)


class NotificationUnreadCountView(APIView):
    """GET /notifications/unread-count/ - return count of unread notifications."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="Get unread notification count",
        responses={200: OpenApiResponse(description="Unread count.")},
    )
    def get(self, request: Request) -> Response:
        """Return the number of unread notifications for the authenticated user."""
        count = _NOTIF_REPO().unread_count(uuid.UUID(str(request.user.id)))
        return success_response({"unread_count": count}, request=request)


class NotificationPreferenceView(APIView):
    """Get or update channel preferences for a notification type."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Preferences"],
        summary="Update notification preferences",
        request=UpdatePreferenceSerializer,
        responses={
            200: OpenApiResponse(description="Preferences updated.", response=_PREF_RESP),
            401: OpenApiResponse(description="Missing or invalid JWT."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def patch(self, request: Request, notification_type: str) -> Response:
        """Upsert channel preferences for the given notification_type."""
        ser = UpdatePreferenceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        entity = _UPDATE_PREF_UC(_PREF_REPO()).execute(
            user_id=uuid.UUID(str(request.user.id)),
            notification_type=notification_type,
            email_enabled=d["email_enabled"],
            push_enabled=d["push_enabled"],
            sms_enabled=d["sms_enabled"],
            in_app_enabled=d["in_app_enabled"],
        )
        return success_response(_PREF_RESP(entity).data, request=request)


class EventJourneyView(APIView):
    """GET/POST /journeys/events/{event_id}/ - create or get the journey for an event."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Intelligent Event Journey"],
        summary="Get event journey",
        description="Return the current journey and stage statuses for an event.",
        responses={
            200: OpenApiResponse(description="Journey returned."),
            404: OpenApiResponse(description="No journey found for this event."),
        },
    )
    def get(self, request: Request, event_id: uuid.UUID) -> Response:
        """Return the journey for the given event."""
        journey = _JOURNEY_REPO().get_by_event(event_id)
        if journey is None:
            return error_response(
                code="ERR_JOURNEY_NOT_FOUND",
                message="No journey found for this event.",
                http_status=404,
                request=request,
            )
        stages_data = [
            {
                "id": str(s.id),
                "stage_type": s.stage_type,
                "trigger_at": s.trigger_at.isoformat(),
                "status": s.status,
                "fired_at": s.fired_at.isoformat() if s.fired_at else None,
            }
            for s in journey.stages
        ]
        return success_response(
            {
                "event_id": str(journey.event_id),
                "event_start": journey.event_start.isoformat(),
                "event_end": journey.event_end.isoformat(),
                "stages": stages_data,
            },
            request=request,
        )

    @extend_schema(
        tags=["Intelligent Event Journey"],
        summary="Create event journey",
        description=(
            "Create an automated notification journey for an event. "
            "Generates 5 stages: pre-event (1 week, 1 day, 1 hour before start), "
            "post-event followup (24h after end), and certificate-ready (48h after end)."
        ),
        responses={
            201: OpenApiResponse(description="Journey created."),
            400: OpenApiResponse(description="Missing or invalid event_start/event_end."),
        },
    )
    def post(self, request: Request, event_id: uuid.UUID) -> Response:
        """Create a new journey for the event from the provided start and end datetimes."""
        from rest_framework import serializers as drf_serializers

        class JourneyCreateSerializer(drf_serializers.Serializer):
            event_start = drf_serializers.DateTimeField()
            event_end = drf_serializers.DateTimeField()

        ser = JourneyCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        journey = _CREATE_JOURNEY_UC(_JOURNEY_REPO()).execute(
            event_id=event_id,
            event_start=d["event_start"],
            event_end=d["event_end"],
        )
        return created_response(
            {"event_id": str(journey.event_id), "stage_count": len(journey.stages)},
            request=request,
        )


class BatchNotificationView(APIView):
    """POST /notifications/batch/ - create the same notification for many users."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="Batch create notifications",
        description=(
            "Send the same notification to up to 1,000 users in a single request. "
            "Users who disabled the given channel are silently skipped."
        ),
        responses={
            201: OpenApiResponse(description="Notifications created."),
        },
    )
    def post(self, request: Request) -> Response:
        """Create one notification per user_id in the batch (capped at 1,000)."""
        from rest_framework import serializers as drf_serializers

        class BatchSerializer(drf_serializers.Serializer):
            user_ids = drf_serializers.ListField(
                child=drf_serializers.UUIDField(), max_length=1000
            )
            notification_type = drf_serializers.CharField(max_length=100)
            channel = drf_serializers.ChoiceField(
                choices=["in_app", "email", "push", "sms"]
            )
            title = drf_serializers.CharField(max_length=255)
            message = drf_serializers.CharField(max_length=2000)
            data = drf_serializers.DictField(required=False, default=dict)

        ser = BatchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        notifications = _BATCH_CREATE_UC(_NOTIF_REPO(), _PREF_REPO()).execute(
            user_ids=d["user_ids"],
            notification_type=d["notification_type"],
            channel=d["channel"],
            title=d["title"],
            message=d["message"],
            data=d.get("data"),
        )
        return created_response(
            {"created": len(notifications)}, request=request
        )
