"""Modèle économique : revenus, dépenses, budget, inflation (section 12)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Economy:
    meal_cost_budget: float
    meal_cost_normal: float
    rent_amount: float
    salary_per_shift: float
    rent_due_day_of_month: int
    inflation_coefficient: float = 1.0
    cumulative_inflation_events: int = 0

    def apply_inflation(self, rate: float) -> None:
        """Applique un coefficient d'inflation périodique aux prix de référence."""
        factor = 1.0 + rate
        self.meal_cost_budget *= factor
        self.meal_cost_normal *= factor
        self.rent_amount *= factor
        self.inflation_coefficient *= factor
        self.cumulative_inflation_events += 1

    def next_rent_due_date(self, current_date) -> "object":
        import datetime as dt

        year, month = current_date.year, current_date.month
        candidate = dt.date(year, month, min(self.rent_due_day_of_month, 28))
        if candidate < current_date:
            month += 1
            if month > 12:
                month = 1
                year += 1
            candidate = dt.date(year, month, min(self.rent_due_day_of_month, 28))
        return candidate
