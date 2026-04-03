"""DRF API views for the audit digest schedule endpoints."""

from __future__ import annotations

import uuid

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.api.responses import created_response, error_response, success_response
from apps.notifications.infrastructure.digest_models import AuditDigestSchedule
from apps.notifications.presentation.digest_serializers import (
    AuditDigestScheduleCreateSerializer,
    AuditDigestSchedulePatchSerializer,
    AuditDigestScheduleResponseSerializer,
)

_RESP = AuditDigestScheduleResponseSerializer


def _serialize_schedule(obj: AuditDigestSchedule) -> dict:
    """Convert an ORM instance to a dict for the response serializer."""
    return {
        "id": str(obj.id),
        "email": obj.email,
        "frequency": obj.frequency,
        "is_active": obj.is_active,
        "created_at": obj.created_at.isoformat(),
        "created_by": str(obj.created_by),
    }


class DigestScheduleListCreateView(APIView):
    """GET /digest-schedules/ list, POST /digest-schedules/ create."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Audit Digest"],
        summary="List all digest schedules",
        description="Returns every audit digest schedule configuration in the system.",
        responses={
            200: OpenApiResponse(description="List of schedules.", response=_RESP(many=True)),
            403: OpenApiResponse(description="Staff access required."),
        },
    )
    def get(self, request: Request) -> Response:
        """Return all digest schedules ordered by creation time."""
        schedules = AuditDigestSchedule.objects.all()
        data = [_serialize_schedule(s) for s in schedules]
        return success_response(data, request=request)

    @extend_schema(
        tags=["Audit Digest"],
        summary="Create a digest schedule",
        description="Saves a new audit digest email schedule configuration.",
        request=AuditDigestScheduleCreateSerializer,
        responses={
            201: OpenApiResponse(description="Schedule created.", response=_RESP),
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Staff access required."),
        },
    )
    def post(self, request: Request) -> Response:
        """Validate payload and persist a new schedule."""
        ser = AuditDigestScheduleCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        schedule = AuditDigestSchedule.objects.create(
            email=d["email"],
            frequency=d["frequency"],
            created_by=d["created_by"],
        )
        return created_response(_serialize_schedule(schedule), request=request)


class DigestScheduleDetailView(APIView):
    """PATCH /digest-schedules/{id}/ update a single schedule."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Audit Digest"],
        summary="Update a digest schedule",
        description="Toggle is_active or change frequency on an existing schedule.",
        request=AuditDigestSchedulePatchSerializer,
        responses={
            200: OpenApiResponse(description="Schedule updated.", response=_RESP),
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Staff access required."),
            404: OpenApiResponse(description="Schedule not found."),
        },
    )
    def patch(self, request: Request, schedule_id: uuid.UUID) -> Response:
        """Apply partial updates to the schedule record."""
        try:
            schedule = AuditDigestSchedule.objects.get(pk=schedule_id)
        except AuditDigestSchedule.DoesNotExist:
            return error_response(
                code="ERR_SCHEDULE_NOT_FOUND",
                message="Digest schedule not found.",
                http_status=404,
                request=request,
            )
        ser = AuditDigestSchedulePatchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        if "frequency" in d:
            schedule.frequency = d["frequency"]
        if "is_active" in d:
            schedule.is_active = d["is_active"]
        schedule.save()
        return success_response(_serialize_schedule(schedule), request=request)
