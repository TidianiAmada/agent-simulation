"""Événement maladie : probabiliste, probabilité croissante avec fatigue/stress élevés (section 11)."""
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from agents.beliefs import BeliefsDelta
from events.base import Event, EventOccurrence

if TYPE_CHECKING:
    from agents.student import Student
    from core.environment import Environment


class IllnessEvent(Event):
    name = "illness"

    def check_and_apply(self, environment: "Environment", student: "Student", dt_hours: float) -> EventOccurrence | None:
        beliefs = student.beliefs
        if beliefs.incapacitated:
            return None  # déjà malade : pas de nouvelle occurrence tant que non rétabli

        base_p = environment.sim_config.illness_base_probability_per_hour
        # La probabilité croît avec une fatigue/un stress déjà élevés (loi utilisée : Bernoulli
        # par heure, dont le paramètre dépend de l'état courant de l'agent - cf. scipy.stats.bernoulli).
        risk_multiplier = 1.0 + max(0.0, beliefs.fatigue - 60.0) / 40.0 + max(0.0, beliefs.stress - 60.0) / 40.0
        p_hour = min(0.05, base_p * risk_multiplier)
        p_interval = self._interval_probability(p_hour, dt_hours)

        if environment.rng.random() >= p_interval:
            return None

        severity = float(environment.rng.uniform(0.3, 1.0))
        beliefs.apply_delta(BeliefsDelta(health=-15.0 * severity, fatigue=10.0 * severity), dt_hours=0.0)
        student.emotion.apply_event_impact(stress_delta=5.0 * severity)
        beliefs.sync_stress(student.emotion.stress)
        recovery_hours = 12.0 + float(environment.rng.uniform(24.0, 72.0)) * severity
        environment.agent_incapacitated_until = beliefs.current_datetime + dt.timedelta(hours=recovery_hours)
        student.notify_significant_event()

        return EventOccurrence(
            name=self.name,
            description=f"Maladie (sévérité {severity:.2f}, {recovery_hours:.0f}h de convalescence)",
            day_index=environment.clock.day_index,
        )
