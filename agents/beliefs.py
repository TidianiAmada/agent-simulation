"""Croyances de l'agent (section 3.1). Mises à jour par perception uniquement,
jamais modifiées directement par les actions (celles-ci passent par des deltas
appliqués via `Beliefs.apply_delta`, orchestré par le cycle cognitif)."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from config.schema import JobStatus
from core.environment import CalendarEvent, Perception


class BeliefsDelta(BaseModel):
    """Variation à appliquer aux croyances suite à l'exécution d'une action ou d'un événement.
    Tous les champs sont additifs sauf les champs explicitement absolus (préfixe `set_`)."""

    money: float = 0.0
    fatigue: float = 0.0
    hunger: float = 0.0
    stress: float = 0.0
    social: float = 0.0
    health: float = 0.0
    sleep_debt: float = 0.0
    last_meal_hours_ago: float = 0.0
    academic_progress: dict[str, float] = Field(default_factory=dict)
    set_job_status: JobStatus | None = None
    set_last_meal_hours_ago: float | None = None


class Beliefs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    money: float
    days_to_next_exam: float = float("inf")
    fatigue: float = 0.0
    hunger: float = 0.0
    stress: float = 0.0
    social: float = 0.0
    health: float = 100.0
    academic_progress: dict[str, float] = Field(default_factory=dict)
    calendar_events: list[CalendarEvent] = Field(default_factory=list)
    job_status: JobStatus = JobStatus.EMPLOYED
    last_meal_hours_ago: float = 0.0
    sleep_debt: float = 0.0

    current_datetime: dt.datetime
    days_to_rent_due: float = float("inf")
    rent_amount: float = 0.0
    weather: str = "sunny"
    incapacitated: bool = False

    def sync_from_perception(self, perception: Perception) -> None:
        self.current_datetime = perception.current_datetime
        self.days_to_next_exam = perception.days_to_next_exam
        self.calendar_events = perception.upcoming_events
        self.days_to_rent_due = perception.days_to_rent_due
        self.rent_amount = perception.rent_amount
        self.weather = perception.weather.value
        self.incapacitated = perception.agent_incapacitated

    def sync_stress(self, stress: float) -> None:
        self.stress = stress

    def apply_delta(self, delta: BeliefsDelta, dt_hours: float) -> None:
        # delta.stress est intentionnellement ignoré ici : le stress est possédé exclusivement
        # par cognition/emotion.py (section 8) ; agents/student.py route delta.stress vers
        # l'émotion, puis `sync_stress` reflète le résultat dans les croyances.
        self.money += delta.money
        self.fatigue = _clamp(self.fatigue + delta.fatigue)
        self.hunger = _clamp(self.hunger + delta.hunger)
        self.social = _clamp(self.social + delta.social)
        self.health = _clamp(self.health + delta.health)
        self.sleep_debt = max(0.0, self.sleep_debt + delta.sleep_debt)
        for subject, gain in delta.academic_progress.items():
            self.academic_progress[subject] = _clamp(self.academic_progress.get(subject, 0.0) + gain)
        if delta.set_job_status is not None:
            self.job_status = delta.set_job_status
        if delta.set_last_meal_hours_ago is not None:
            self.last_meal_hours_ago = delta.set_last_meal_hours_ago
        else:
            self.last_meal_hours_ago += dt_hours


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))
