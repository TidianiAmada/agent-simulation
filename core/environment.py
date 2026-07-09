"""État du monde partagé (section 2 / core/environment.py)."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from config.schema import AgentProfile, SimulationConfig
from core.clock import Period, SimClock
from models.economy import Economy


class CalendarEventType(str, Enum):
    EXAM = "exam"
    RENT_DUE = "rent_due"


@dataclass
class CalendarEvent:
    type: CalendarEventType
    date: dt.date
    subject: str | None = None
    description: str = ""


class Weather(str, Enum):
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"


@dataclass
class Perception:
    """Instantané perçu par l'agent à un instant donné (lecture seule)."""

    current_datetime: dt.datetime
    day_index: int
    hour_of_day: float
    weekday: int
    is_weekend: bool
    period: Period
    weather: Weather
    meal_cost_budget: float
    meal_cost_normal: float
    rent_amount: float
    salary_per_shift: float
    upcoming_events: list[CalendarEvent]
    next_exam: CalendarEvent | None
    days_to_next_exam: float
    next_rent_due: dt.date
    days_to_rent_due: float
    agent_incapacitated: bool


class Environment:
    """Référentiel du monde : calendrier, prix, météo, lieux. Ne connaît pas les beliefs de l'agent."""

    LOCATIONS = ("home", "campus", "workplace", "shops")

    def __init__(self, sim_config: SimulationConfig, agent_profile: AgentProfile, clock: SimClock, rng: np.random.Generator):
        self.clock = clock
        self.rng = rng
        self.sim_config = sim_config
        self.subjects = list(agent_profile.subjects)
        self.economy = Economy(
            meal_cost_budget=agent_profile.meal_cost_budget,
            meal_cost_normal=agent_profile.meal_cost_normal,
            rent_amount=agent_profile.rent_amount,
            salary_per_shift=agent_profile.salary_per_shift,
            rent_due_day_of_month=sim_config.rent_due_day_of_month,
        )
        self.exam_dates: dict[str, list[dt.date]] = self._build_exam_calendar()
        self.rent_due_dates: list[dt.date] = self._build_rent_calendar()
        self._weather_cache_day: int | None = None
        self._weather_today: Weather = Weather.SUNNY
        self.agent_incapacitated_until: dt.datetime | None = None
        self.exams_resolved: set[tuple[str, dt.date]] = set()
        self.rent_paid_dates: set[dt.date] = set()

    def _build_exam_calendar(self) -> dict[str, list[dt.date]]:
        exam_dates: dict[str, list[dt.date]] = {s: [] for s in self.subjects}
        for start_day, end_day in self.clock.calendar.exam_session_days:
            span = max(1, end_day - start_day)
            for i, subject in enumerate(self.subjects):
                offset_day = start_day + (i % span)
                exam_dates[subject].append(self.clock.start_date + dt.timedelta(days=offset_day))
        return exam_dates

    def _build_rent_calendar(self) -> list[dt.date]:
        dates = []
        current = self.economy.next_rent_due_date(self.clock.start_date)
        end_date = self.clock.start_date + dt.timedelta(days=self.clock.duration_days)
        while current <= end_date:
            dates.append(current)
            month = current.month + 1
            year = current.year
            if month > 12:
                month = 1
                year += 1
            current = dt.date(year, month, min(self.sim_config.rent_due_day_of_month, 28))
        return dates

    def _refresh_weather(self) -> None:
        day = self.clock.day_index
        if self._weather_cache_day == day:
            return
        self._weather_cache_day = day
        self._weather_today = Weather(self.rng.choice(["sunny", "cloudy", "rainy"], p=[0.5, 0.3, 0.2]))

    def _next_exam(self, now: dt.date) -> CalendarEvent | None:
        candidates = []
        for subject, dates in self.exam_dates.items():
            for d in dates:
                if d >= now and (subject, d) not in self.exams_resolved:
                    candidates.append(CalendarEvent(CalendarEventType.EXAM, d, subject, f"Examen de {subject}"))
        if not candidates:
            return None
        return min(candidates, key=lambda e: e.date)

    def _next_rent_due(self, now: dt.date) -> dt.date:
        for d in self.rent_due_dates:
            if d >= now:
                return d
        return self.rent_due_dates[-1] if self.rent_due_dates else now

    def perceive(self) -> Perception:
        self._refresh_weather()
        now_dt = self.clock.current_datetime
        now_date = now_dt.date()
        next_exam = self._next_exam(now_date)
        next_rent = self._next_rent_due(now_date)
        days_to_exam = (next_exam.date - now_date).days if next_exam else float("inf")
        days_to_rent = (next_rent - now_date).days

        horizon = now_date + dt.timedelta(days=30)
        upcoming: list[CalendarEvent] = []
        for subject, dates in self.exam_dates.items():
            for d in dates:
                if now_date <= d <= horizon and (subject, d) not in self.exams_resolved:
                    upcoming.append(CalendarEvent(CalendarEventType.EXAM, d, subject, f"Examen de {subject}"))
        for d in self.rent_due_dates:
            if now_date <= d <= horizon:
                upcoming.append(CalendarEvent(CalendarEventType.RENT_DUE, d, description="Loyer dû"))
        upcoming.sort(key=lambda e: e.date)

        incapacitated = self.agent_incapacitated_until is not None and now_dt < self.agent_incapacitated_until

        return Perception(
            current_datetime=now_dt,
            day_index=self.clock.day_index,
            hour_of_day=self.clock.hour_of_day,
            weekday=self.clock.weekday,
            is_weekend=self.clock.is_weekend,
            period=self.clock.current_period(),
            weather=self._weather_today,
            meal_cost_budget=self.economy.meal_cost_budget,
            meal_cost_normal=self.economy.meal_cost_normal,
            rent_amount=self.economy.rent_amount,
            salary_per_shift=self.economy.salary_per_shift,
            upcoming_events=upcoming,
            next_exam=next_exam,
            days_to_next_exam=days_to_exam,
            next_rent_due=next_rent,
            days_to_rent_due=days_to_rent,
            agent_incapacitated=incapacitated,
        )
