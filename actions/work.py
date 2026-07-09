from __future__ import annotations

from typing import TYPE_CHECKING

from actions.base import Action, ActionCategory
from agents.beliefs import BeliefsDelta
from config.schema import JobStatus

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from core.environment import Environment


class WorkShift(Action):
    name = "work.shift"
    category = ActionCategory.WORK
    min_duration = 4.0
    max_duration = 4.0
    fatigue_threshold = 85.0
    base_satisfaction = 0.3

    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        return (
            beliefs.job_status == JobStatus.EMPLOYED
            and beliefs.fatigue < self.fatigue_threshold
            and not beliefs.incapacitated
        )

    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        scale = duration / 4.0
        return BeliefsDelta(
            money=environment.economy.salary_per_shift * scale,
            fatigue=12.0 * scale,
            stress=4.0 * scale,
        )
