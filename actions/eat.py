from __future__ import annotations

from typing import TYPE_CHECKING

from actions.base import Action, ActionCategory
from agents.beliefs import BeliefsDelta

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from core.environment import Environment


class BudgetMeal(Action):
    name = "eat.budget_meal"
    category = ActionCategory.OTHER
    min_duration = 0.5
    max_duration = 0.5
    base_satisfaction = 0.2

    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        return beliefs.money >= environment.economy.meal_cost_budget

    def cost(self, beliefs: "Beliefs", environment: "Environment") -> float:
        return environment.economy.meal_cost_budget

    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        return BeliefsDelta(
            money=-environment.economy.meal_cost_budget,
            hunger=-40.0,
            health=1.0,
            set_last_meal_hours_ago=0.0,
        )


class NormalMeal(Action):
    name = "eat.normal_meal"
    category = ActionCategory.OTHER
    min_duration = 1.0
    max_duration = 1.0
    base_satisfaction = 0.5

    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        return beliefs.money >= environment.economy.meal_cost_normal

    def cost(self, beliefs: "Beliefs", environment: "Environment") -> float:
        return environment.economy.meal_cost_normal

    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        return BeliefsDelta(
            money=-environment.economy.meal_cost_normal,
            hunger=-55.0,
            health=3.0,
            set_last_meal_hours_ago=0.0,
        )
