"""Événement loyer : calendaire (mensuel), pénalité en cas de non-paiement (section 11)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from agents.beliefs import BeliefsDelta
from events.base import Event, EventOccurrence

if TYPE_CHECKING:
    from agents.student import Student
    from core.environment import Environment


class RentEvent(Event):
    name = "rent"

    def check_and_apply(self, environment: "Environment", student: "Student", dt_hours: float) -> EventOccurrence | None:
        beliefs = student.beliefs
        now_date = beliefs.current_datetime.date()
        last_occurrence: EventOccurrence | None = None

        for due_date in environment.rent_due_dates:
            if due_date in environment.rent_paid_dates or due_date > now_date:
                continue

            rent = environment.economy.rent_amount
            if beliefs.money >= rent:
                beliefs.apply_delta(BeliefsDelta(money=-rent), dt_hours=0.0)
                description = f"Loyer payé ({rent:.0f})"
            else:
                # Non-paiement : le loyer est tout de même prélevé (dette, money peut devenir
                # négatif - section 17) et une pénalité (stress, risque d'expulsion simulé) s'applique.
                beliefs.apply_delta(BeliefsDelta(money=-rent, health=-3.0), dt_hours=0.0)
                student.emotion.apply_event_impact(stress_delta=15.0)
                beliefs.sync_stress(student.emotion.stress)
                description = f"Loyer impayé à l'échéance ({rent:.0f}) : pénalité"
                student.notify_significant_event()

            environment.rent_paid_dates.add(due_date)
            last_occurrence = EventOccurrence(name=self.name, description=description, day_index=environment.clock.day_index)

        return last_occurrence
