"""Unit tests for the Intelligent Event Journey feature."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _event_start(days_from_now: int = 14) -> datetime:
    return _now() + timedelta(days=days_from_now)


def test_create_journey_produces_five_stages():
    """CreateEventJourneyUseCase creates pre_event_week, pre_event_day, pre_event_hour,
    post_event_followup, and certificate_ready stages."""
    from apps.notifications.application.use_cases.create_journey import CreateEventJourneyUseCase
    from apps.notifications.tests.unit.fakes import FakeJourneyRepository

    start = _event_start(14)
    end = start + timedelta(hours=3)
    repo = FakeJourneyRepository()

    journey = CreateEventJourneyUseCase(repo).execute(
        event_id=uuid.uuid4(), event_start=start, event_end=end
    )

    stage_types = {s.stage_type for s in journey.stages}
    assert "pre_event_week" in stage_types
    assert "pre_event_day" in stage_types
    assert "pre_event_hour" in stage_types
    assert "post_event_followup" in stage_types
    assert "certificate_ready" in stage_types
    assert len(journey.stages) == 5


def test_pre_event_week_triggers_7_days_before_start():
    """pre_event_week stage trigger_at is exactly 7 days before event start."""
    from apps.notifications.application.use_cases.create_journey import CreateEventJourneyUseCase
    from apps.notifications.tests.unit.fakes import FakeJourneyRepository

    start = _event_start(14)
    end = start + timedelta(hours=3)
    journey = CreateEventJourneyUseCase(FakeJourneyRepository()).execute(
        event_id=uuid.uuid4(), event_start=start, event_end=end
    )

    week_stage = next(s for s in journey.stages if s.stage_type == "pre_event_week")
    diff = start - week_stage.trigger_at
    assert abs(diff.total_seconds() - 7 * 24 * 3600) < 1


def test_post_event_followup_triggers_24_hours_after_end():
    """post_event_followup stage trigger_at is 24 hours after event end."""
    from apps.notifications.application.use_cases.create_journey import CreateEventJourneyUseCase
    from apps.notifications.tests.unit.fakes import FakeJourneyRepository

    start = _event_start(14)
    end = start + timedelta(hours=3)
    journey = CreateEventJourneyUseCase(FakeJourneyRepository()).execute(
        event_id=uuid.uuid4(), event_start=start, event_end=end
    )

    followup = next(s for s in journey.stages if s.stage_type == "post_event_followup")
    diff = followup.trigger_at - end
    assert abs(diff.total_seconds() - 24 * 3600) < 1


def test_get_due_stages_returns_past_pending_stages():
    """GetDueStagesUseCase returns only pending stages whose trigger_at is in the past."""
    from apps.notifications.application.use_cases.create_journey import CreateEventJourneyUseCase
    from apps.notifications.application.use_cases.get_due_stages import GetDueStagesUseCase
    from apps.notifications.tests.unit.fakes import FakeJourneyRepository

    # event that started 2 days ago - week/day/hour stages are all past due
    start = _now() - timedelta(days=2)
    end = start + timedelta(hours=3)
    repo = FakeJourneyRepository()
    CreateEventJourneyUseCase(repo).execute(event_id=uuid.uuid4(), event_start=start, event_end=end)

    due = GetDueStagesUseCase(repo).execute(as_of=_now())
    assert len(due) > 0
    for stage in due:
        assert stage.trigger_at <= _now()
        assert stage.status == "pending"


def test_new_journey_all_stages_pending():
    """All stages start with status pending."""
    from apps.notifications.application.use_cases.create_journey import CreateEventJourneyUseCase
    from apps.notifications.tests.unit.fakes import FakeJourneyRepository

    start = _event_start(14)
    end = start + timedelta(hours=3)
    journey = CreateEventJourneyUseCase(FakeJourneyRepository()).execute(
        event_id=uuid.uuid4(), event_start=start, event_end=end
    )
    for stage in journey.stages:
        assert stage.status == "pending"
