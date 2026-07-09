"""Événement examen : calendaire (planifié) + variante "examen surprise" (section 11)."""
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from core.clock import Period
from events.base import Event, EventOccurrence

if TYPE_CHECKING:
    from agents.student import Student
    from core.environment import Environment

PASS_THRESHOLD = 50.0


class ExamEvent(Event):
    name = "exam"

    def check_and_apply(self, environment: "Environment", student: "Student", dt_hours: float) -> EventOccurrence | None:
        beliefs = student.beliefs
        now_date = beliefs.current_datetime.date()
        last_occurrence: EventOccurrence | None = None

        for subject, dates in environment.exam_dates.items():
            for exam_date in list(dates):
                if (subject, exam_date) in environment.exams_resolved:
                    continue
                if exam_date > now_date:
                    continue
                last_occurrence = self._resolve_exam(environment, student, subject, exam_date)

        surprise = self._maybe_trigger_surprise_exam(environment, student, dt_hours)
        return surprise or last_occurrence

    def _resolve_exam(self, environment: "Environment", student: "Student", subject: str, exam_date: dt.date) -> EventOccurrence:
        beliefs = student.beliefs
        progress = beliefs.academic_progress.get(subject, 0.0)
        # Bruit gaussien représentant l'aléa de l'épreuve (scipy.stats.norm) ; le stress pénalise le score.
        noise = float(environment.rng.normal(0.0, 8.0))
        score = max(0.0, min(100.0, progress - 0.15 * beliefs.stress + noise))
        passed = score >= PASS_THRESHOLD

        environment.exams_resolved.add((subject, exam_date))
        student.exam_results.append(
            {
                "subject": subject,
                "date": exam_date.isoformat(),
                "score": round(score, 1),
                "passed": passed,
            }
        )
        student.emotion.apply_event_impact(stress_delta=-5.0 if passed else 8.0)
        beliefs.sync_stress(student.emotion.stress)
        student.notify_significant_event()

        verdict = "réussi" if passed else "échoué"
        return EventOccurrence(
            name=self.name,
            description=f"Examen de {subject} {verdict} (score {score:.1f})",
            day_index=environment.clock.day_index,
        )

    def _maybe_trigger_surprise_exam(self, environment: "Environment", student: "Student", dt_hours: float) -> EventOccurrence | None:
        if environment.clock.current_period() != Period.COURSES:
            return None
        p_hour = environment.sim_config.exam_surprise_probability_per_hour
        p_interval = self._interval_probability(p_hour, dt_hours)
        if environment.rng.random() >= p_interval:
            return None

        subject = str(environment.rng.choice(environment.subjects))
        days_ahead = int(environment.rng.integers(1, 4))
        surprise_date = student.beliefs.current_datetime.date() + dt.timedelta(days=days_ahead)
        environment.exam_dates.setdefault(subject, []).append(surprise_date)
        student.notify_significant_event()

        return EventOccurrence(
            name="exam_surprise",
            description=f"Examen surprise annoncé : {subject} dans {days_ahead} jour(s)",
            day_index=environment.clock.day_index,
        )
