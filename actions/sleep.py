from __future__ import annotations

from typing import TYPE_CHECKING

from actions.base import Action, ActionCategory
from agents.beliefs import BeliefsDelta

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from core.environment import Environment


class Sleep(Action):
    name = "sleep.sleep"
    category = ActionCategory.SLEEP
    min_duration = 6.0
    max_duration = 8.0
    base_satisfaction = 0.4
    emergency_sleep_debt = 8.0

    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        perception = environment.perceive()
        is_night = perception.hour_of_day >= 22 or perception.hour_of_day < 7
        return is_night or beliefs.sleep_debt >= self.emergency_sleep_debt

    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        return BeliefsDelta(
            fatigue=-11.0 * duration,
            sleep_debt=-1.2 * duration,
            health=1.5,
        )
