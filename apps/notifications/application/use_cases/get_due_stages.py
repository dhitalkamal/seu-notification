"""Use case: get journey stages that are due to fire as of a given timestamp."""

from __future__ import annotations

from datetime import datetime

from apps.notifications.domain.entities import JourneyStageEntity
from apps.notifications.domain.repositories import IEventJourneyRepository


class GetDueStagesUseCase:
    """Return all pending journey stages whose trigger_at has passed."""

    def __init__(self, repo: IEventJourneyRepository) -> None:
        self._repo = repo

    def execute(self, *, as_of: datetime) -> list[JourneyStageEntity]:
        """Return pending stages with trigger_at on or before as_of."""
        return self._repo.get_due_stages(as_of)
