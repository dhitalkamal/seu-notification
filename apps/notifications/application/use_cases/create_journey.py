"""Use case: create an Intelligent Event Journey for a newly published event."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from apps.notifications.domain.entities import EventJourneyEntity, JourneyStageEntity
from apps.notifications.domain.repositories import IEventJourneyRepository

_STAGES = [
    ("pre_event_week", timedelta(days=-7)),
    ("pre_event_day", timedelta(days=-1)),
    ("pre_event_hour", timedelta(hours=-1)),
    ("post_event_followup", timedelta(hours=24)),
    ("certificate_ready", timedelta(hours=48)),
]


class CreateEventJourneyUseCase:
    """Create automated notification stages for an event based on its start and end times."""

    def __init__(self, repo: IEventJourneyRepository) -> None:
        self._repo = repo

    def execute(
        self,
        *,
        event_id: uuid.UUID,
        event_start: datetime,
        event_end: datetime,
    ) -> EventJourneyEntity:
        """
        Generate five journey stages anchored on event_start and event_end.

        Pre-event stages use negative offsets from start_date.
        Post-event stages use positive offsets from end_date.
        All stages are created with status=pending.
        """
        now = datetime.now(timezone.utc)
        stages = []

        for stage_type, delta in _STAGES:
            if stage_type.startswith("pre_event"):
                trigger_at = event_start + delta
            else:
                trigger_at = event_end + delta

            stages.append(
                JourneyStageEntity(
                    id=uuid.uuid4(),
                    event_id=event_id,
                    stage_type=stage_type,
                    trigger_at=trigger_at,
                    status="pending",
                    created_at=now,
                )
            )

        journey = EventJourneyEntity(
            id=uuid.uuid4(),
            event_id=event_id,
            event_start=event_start,
            event_end=event_end,
            created_at=now,
            stages=stages,
        )
        return self._repo.create(journey)
