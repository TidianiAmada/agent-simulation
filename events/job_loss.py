"""Événement bonus : perte d'emploi étudiant, probabiliste (section 11)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from agents.beliefs import BeliefsDelta
from config.schema import JobStatus
from events.base import Event, EventOccurrence

if TYPE_CHECKING:
    from agents.student import Student
    from core.environment import Environment


class JobLossEvent(Event):
    name = "job_loss"

    def check_and_apply(self, environment: "Environment", student: "Student", dt_hours: float) -> EventOccurrence | None:
        beliefs = student.beliefs
        if beliefs.job_status != JobStatus.EMPLOYED:
            return None

        p_hour = environment.sim_config.job_loss_probability_per_hour
        p_interval = self._interval_probability(p_hour, dt_hours)
        if environment.rng.random() >= p_interval:
            return None

        beliefs.apply_delta(BeliefsDelta(set_job_status=JobStatus.UNEMPLOYED), dt_hours=0.0)
        student.emotion.apply_event_impact(stress_delta=20.0)
        beliefs.sync_stress(student.emotion.stress)
        student.notify_significant_event()

        return EventOccurrence(name=self.name, description="Perte de l'emploi étudiant", day_index=environment.clock.day_index)
