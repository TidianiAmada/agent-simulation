"""Horloge de simulation (section 2 / core/clock.py).

L'horloge avance par pas variables (la durée de l'action choisie par l'agent),
la granularité "1 heure" du cahier des charges servant d'unité de référence
pour les taux de dégradation des besoins et les probabilités d'événements,
plutôt que d'imposer un pas fixe qui obligerait à fragmenter les actions
multi-heures en plusieurs cycles de décision identiques.
"""
from __future__ import annotations

import datetime as dt
from enum import Enum


class Period(str, Enum):
    COURSES = "courses"
    EXAMS = "exams"
    VACATION = "vacation"


class AcademicCalendar:
    """Découpage simple de l'année universitaire en périodes (jours depuis le début)."""

    # Fractions d'une année académique de référence (270 jours, septembre -> juin, section 2/9) :
    # cours S1 / examens S1 / vacances / cours S2 / examens S2. Exprimées en proportions pour que
    # le calendrier reste cohérent même sur une durée de simulation raccourcie (tests, calibrage).
    _REFERENCE_DAYS = 270.0
    _BOUNDARIES = (119, 133, 147, 263)

    def __init__(self, duration_days: int):
        scale = duration_days / self._REFERENCE_DAYS
        raw = [max(1, round(b * scale)) for b in self._BOUNDARIES]
        # Garantit des bornes strictement croissantes et bornées par duration_days, même
        # pour des durées de simulation très courtes (tests).
        bounded: list[int] = []
        previous = 0
        for value in raw:
            value = min(duration_days, max(value, previous + 1 if previous < duration_days else previous))
            bounded.append(value)
            previous = value
        s1_courses_end, s1_exams_end, break_end, s2_courses_end = bounded
        s2_exams_end = duration_days

        self.periods: list[tuple[int, int, Period]] = [
            (0, s1_courses_end, Period.COURSES),
            (s1_courses_end, s1_exams_end, Period.EXAMS),
            (s1_exams_end, break_end, Period.VACATION),
            (break_end, s2_courses_end, Period.COURSES),
            (s2_courses_end, s2_exams_end, Period.EXAMS),
        ]
        self.exam_session_days: list[tuple[int, int]] = [
            (s1_courses_end, s1_exams_end),
            (s2_courses_end, s2_exams_end),
        ]

    def period_at(self, day_index: int) -> Period:
        for start, end, period in self.periods:
            if start <= day_index < end:
                return period
        return Period.VACATION


class SimClock:
    def __init__(self, start_date: dt.date, duration_days: int, time_step_hours: float = 1.0):
        self.start_date = start_date
        self.duration_days = duration_days
        self.time_step_hours = time_step_hours
        self.total_hours = duration_days * 24.0
        self.elapsed_hours = 0.0
        self.calendar = AcademicCalendar(duration_days)

    @property
    def current_datetime(self) -> dt.datetime:
        return dt.datetime.combine(self.start_date, dt.time.min) + dt.timedelta(hours=self.elapsed_hours)

    @property
    def day_index(self) -> int:
        return int(self.elapsed_hours // 24)

    @property
    def hour_of_day(self) -> float:
        return self.elapsed_hours % 24

    @property
    def weekday(self) -> int:
        return self.current_datetime.weekday()

    @property
    def is_weekend(self) -> bool:
        return self.weekday >= 5

    def current_period(self) -> Period:
        return self.calendar.period_at(self.day_index)

    def is_finished(self) -> bool:
        return self.elapsed_hours >= self.total_hours

    def advance(self, dt_hours: float) -> None:
        if dt_hours <= 0:
            raise ValueError("dt_hours doit être strictement positif")
        self.elapsed_hours += dt_hours

    def remaining_hours(self) -> float:
        return max(0.0, self.total_hours - self.elapsed_hours)
