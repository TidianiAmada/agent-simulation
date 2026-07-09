from __future__ import annotations

from typing import TYPE_CHECKING

from actions.base import Action, ActionCategory
from agents.beliefs import BeliefsDelta

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from core.environment import Environment


class Rest(Action):
    """Détente gratuite (à domicile) : réduit le stress sans coût financier."""

    name = "leisure.rest"
    category = ActionCategory.LEISURE
    min_duration = 1.0
    max_duration = 2.0
    base_satisfaction = 0.5

    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        return not beliefs.incapacitated

    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        return BeliefsDelta(stress=-10.0 * duration, social=1.0 * duration)


class Socialize(Action):
    """Sortie sociale payante : réduit le stress et l'isolement social."""

    name = "leisure.socialize"
    category = ActionCategory.LEISURE
    min_duration = 1.0
    max_duration = 3.0
    base_satisfaction = 0.7
    outing_cost = 1500.0

    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        return not beliefs.incapacitated and beliefs.money >= self.outing_cost

    def cost(self, beliefs: "Beliefs", environment: "Environment") -> float:
        return self.outing_cost

    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        return BeliefsDelta(
            money=-self.outing_cost,
            stress=-8.0 * duration,
            social=-15.0 * duration,
        )
