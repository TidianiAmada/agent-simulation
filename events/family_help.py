"""Événement bonus : aide familiale exceptionnelle, probabiliste et spontanée (section 11).

Distinct de `actions/finance.py::RequestFamilyHelp`, qui modélise une sollicitation
délibérée de l'agent (méthode HTN), alors qu'ici l'aide survient sans initiative
de l'agent.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from agents.beliefs import BeliefsDelta
from events.base import Event, EventOccurrence

if TYPE_CHECKING:
    from agents.student import Student
    from core.environment import Environment


class FamilyHelpEvent(Event):
    name = "family_help"

    def check_and_apply(self, environment: "Environment", student: "Student", dt_hours: float) -> EventOccurrence | None:
        p_hour = environment.sim_config.family_help_probability_per_hour
        p_interval = self._interval_probability(p_hour, dt_hours)
        if environment.rng.random() >= p_interval:
            return None

        amount = float(environment.rng.uniform(5000.0, 20000.0))
        student.beliefs.apply_delta(BeliefsDelta(money=amount), dt_hours=0.0)
        student.emotion.apply_event_impact(stress_delta=-8.0)
        student.beliefs.sync_stress(student.emotion.stress)

        return EventOccurrence(
            name=self.name,
            description=f"Aide familiale exceptionnelle reçue (+{amount:.0f})",
            day_index=environment.clock.day_index,
        )
