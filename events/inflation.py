"""Événement inflation : périodique, augmente le coût des repas/loyer (section 11)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from events.base import Event, EventOccurrence

if TYPE_CHECKING:
    from agents.student import Student
    from core.environment import Environment


class InflationEvent(Event):
    name = "inflation"

    def __init__(self) -> None:
        self._last_applied_day = 0

    def check_and_apply(self, environment: "Environment", student: "Student", dt_hours: float) -> EventOccurrence | None:
        day = environment.clock.day_index
        period = environment.sim_config.inflation_period_days
        if day - self._last_applied_day < period:
            return None

        self._last_applied_day = day
        rate = max(0.0, float(environment.rng.normal(
            environment.sim_config.inflation_rate_mean,
            environment.sim_config.inflation_rate_std,
        )))
        environment.economy.apply_inflation(rate)

        return EventOccurrence(
            name=self.name,
            description=f"Inflation : +{rate * 100:.1f}% sur les prix de référence",
            day_index=day,
        )
