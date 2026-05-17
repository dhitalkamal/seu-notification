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

from apps.common.api.pagination import StandardPagination
from apps.common.api.responses import created_response, error_response, success_response
from apps.common.health import check_database, check_rabbitmq, check_redis
from apps.notifications.application.use_cases.create_notification import CreateNotificationUseCase
from apps.notifications.application.use_cases.mark_all_read import MarkAllReadUseCase
from apps.notifications.application.use_cases.mark_read import MarkNotificationReadUseCase
from apps.notifications.infrastructure.publisher import RabbitMQPublisher
from apps.notifications.infrastructure.repositories import (
    DjangoNotificationPreferenceRepository,
    DjangoNotificationRepository,
)
from apps.notifications.presentation.serializers import (
    CreateNotificationSerializer,
    MarkAllReadResponseSerializer,
    NotificationResponseSerializer,
)

_IS_AUTH = IsAuthenticated
_CREATED = created_response
_UUID = uuid.UUID
_PAGINATION = StandardPagination
_CREATE_UC = CreateNotificationUseCase
_MARK_READ_UC = MarkNotificationReadUseCase
_MARK_ALL_UC = MarkAllReadUseCase
_NOTIF_REPO = DjangoNotificationRepository
_PREF_REPO = DjangoNotificationPreferenceRepository
_PUBLISHER = RabbitMQPublisher
_CREATE_SER = CreateNotificationSerializer
_NOTIF_RESP_SER = NotificationResponseSerializer
_MARK_ALL_RESP_SER = MarkAllReadResponseSerializer

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
    """List own notifications or create a new notification."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="List own notifications",
        description="Returns all notifications for the authenticated user, newest first, paginated.",
        responses={
            200: OpenApiResponse(
                description="Paginated notification list.", response=_NOTIF_RESP_SER(many=True)
            ),
            401: OpenApiResponse(description="Missing or invalid JWT."),
        },
    )
    def get(self, request: Request) -> Response:
        """Return paginated notifications scoped to the authenticated user."""
        user_id = _UUID(str(request.user.id))
        notifications = _NOTIF_REPO().list_by_user(user_id)
        paginator = _PAGINATION()
        page = paginator.paginate_queryset(notifications, request)
        return paginator.get_paginated_response(_NOTIF_RESP_SER(page, many=True).data)

    @extend_schema(
        tags=["Notifications"],
        summary="Create a notification",
        description=(
            "Creates a notification for the given user_id. "
            "In-app: status=delivered immediately. "
            "Email: status=pending, published to RabbitMQ for async delivery. "
            "Channel disabled in preferences: status=failed."
        ),
        request=_CREATE_SER,
        responses={
            201: OpenApiResponse(description="Notification created.", response=_NOTIF_RESP_SER),
            401: OpenApiResponse(description="Missing or invalid JWT."),
        },
    )
    def post(self, request: Request) -> Response:
        """Create and deliver a notification based on channel type."""
        ser = _CREATE_SER(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        result = _CREATE_UC(
            notif_repo=_NOTIF_REPO(),
            pref_repo=_PREF_REPO(),
            publisher=_PUBLISHER(),
        ).execute(
            user_id=d["user_id"],
            notification_type=d["notification_type"],
            channel=d["channel"],
            title=d["title"],
            message=d["message"],
            data=d["data"],
        )
        return _CREATED(_NOTIF_RESP_SER(result).data, request=request)


class MarkNotificationReadView(APIView):
    """Mark a single notification as read."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="Mark notification as read",
        request=None,
        responses={
            200: OpenApiResponse(description="Notification marked read.", response=_NOTIF_RESP_SER),
            401: OpenApiResponse(description="Missing or invalid JWT."),
            404: OpenApiResponse(description="Notification not found."),
        },
    )
    def post(self, request: Request, notification_id: uuid.UUID) -> Response:
        """Mark the given notification as read for the authenticated user."""
        result = _MARK_READ_UC(_NOTIF_REPO()).execute(
            notification_id=notification_id,
            user_id=_UUID(str(request.user.id)),
        )
        return success_response(_NOTIF_RESP_SER(result).data, request=request)


class MarkAllReadView(APIView):
    """Mark all of the authenticated user's unread notifications as read."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="Mark all notifications as read",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Count of newly-read notifications.", response=_MARK_ALL_RESP_SER
            ),
            401: OpenApiResponse(description="Missing or invalid JWT."),
        },
    )
    def post(self, request: Request) -> Response:
        """Bulk-mark all unread notifications and return the count."""
        count = _MARK_ALL_UC(_NOTIF_REPO()).execute(user_id=_UUID(str(request.user.id)))
        return success_response({"count": count}, request=request)
