from __future__ import annotations

from typing import TYPE_CHECKING

from actions.base import Action, ActionCategory
from agents.beliefs import BeliefsDelta
from core.clock import Period
from core.environment import CalendarEventType

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from core.environment import Environment


def target_subject(beliefs: "Beliefs") -> str | None:
    """Choisit la matière la plus urgente (examen le plus proche), sinon la moins avancée."""
    if not beliefs.academic_progress:
        return None
    exam_events = [e for e in beliefs.calendar_events if e.type == CalendarEventType.EXAM and e.subject]
    if exam_events:
        nearest = min(exam_events, key=lambda e: e.date)
        return nearest.subject
    return min(beliefs.academic_progress, key=lambda s: beliefs.academic_progress[s])


class AttendCourse(Action):
    name = "study.attend_course"
    category = ActionCategory.STUDY
    min_duration = 2.0
    max_duration = 3.0
    base_satisfaction = 0.2

    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        if beliefs.incapacitated:
            return False
        perception = environment.perceive()
        in_course_hours = (8 <= perception.hour_of_day < 12) or (14 <= perception.hour_of_day < 17)
        return perception.period == Period.COURSES and not perception.is_weekend and in_course_hours

    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        subject = target_subject(beliefs)
        gains = {subject: 3.0 * (duration / 2.5)} if subject else {}
        return BeliefsDelta(academic_progress=gains, fatigue=6.0 * (duration / 2.5))


class Review(Action):
    name = "study.review"
    category = ActionCategory.STUDY
    min_duration = 1.0
    max_duration = 3.0
    fatigue_threshold = 80.0
    base_satisfaction = 0.35

    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        return beliefs.fatigue < self.fatigue_threshold and not beliefs.incapacitated

    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        subject = target_subject(beliefs)
        gains = {subject: 5.0 * duration} if subject else {}
        intensive = duration > 2.0
        return BeliefsDelta(
            academic_progress=gains,
            fatigue=5.0 * duration,
            stress=3.0 * duration if intensive else 1.0 * duration,
        )
