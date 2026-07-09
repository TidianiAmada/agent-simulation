"""Planificateur HTN simplifié (section 5) : décompose le désir dominant en intention concrète."""
from __future__ import annotations

from typing import TYPE_CHECKING

from actions.eat import BudgetMeal, NormalMeal
from actions.finance import RequestFamilyHelp
from actions.leisure import Rest, Socialize
from actions.sleep import Sleep
from actions.study import AttendCourse, Review
from actions.work import WorkShift
from agents.intentions import Intention
from config.schema import NTAConfig

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from agents.desires import Desire
    from core.environment import Environment

# Instances réutilisées (les actions sont sans état propre : le contexte est passé à l'appel).
_WORK = WorkShift()
_BUDGET_MEAL = BudgetMeal()
_NORMAL_MEAL = NormalMeal()
_ATTEND_COURSE = AttendCourse()
_REVIEW = Review()
_SLEEP = Sleep()
_REST = Rest()
_SOCIALIZE = Socialize()
_FAMILY_HELP = RequestFamilyHelp()


class HTNPlanner:
    def __init__(self, nta: NTAConfig):
        self.nta = nta

    def decompose(self, desire: "Desire", beliefs: "Beliefs", environment: "Environment", day_index: int) -> Intention:
        method = getattr(self, f"_method_{desire.name}", self._method_default)
        plan = method(beliefs, environment)
        return Intention(goal_name=desire.name, plan=plan, created_at_day=day_index)

    # -- Réussir l'examen : assister aux cours si créneau dispo, sinon réviser (section 5.1).
    def _method_reussir_examen(self, beliefs: "Beliefs", environment: "Environment") -> list:
        return [_ATTEND_COURSE, _REVIEW]

    # -- Payer le loyer (section 5.2) : payer directement (rien à faire, l'événement rent.py
    # règle le paiement automatiquement si solvable) / travailler / solliciter la famille.
    def _method_payer_loyer(self, beliefs: "Beliefs", environment: "Environment") -> list:
        if beliefs.money >= beliefs.rent_amount:
            return [_WORK]  # solvable : on continue de travailler normalement en attendant l'échéance
        if beliefs.days_to_rent_due > 3:
            return [_WORK]
        return [_FAMILY_HELP, _WORK]

    # -- Rester en bonne santé : dormir si fatigue/dette de sommeil élevées, sinon se détendre.
    def _method_rester_en_bonne_sante(self, beliefs: "Beliefs", environment: "Environment") -> list:
        if beliefs.sleep_debt > 4.0 or beliefs.fatigue >= self.nta.fatigue.alert:
            return [_SLEEP]
        return [_REST, _SOCIALIZE]

    def _method_se_nourrir(self, beliefs: "Beliefs", environment: "Environment") -> list:
        return [_BUDGET_MEAL, _NORMAL_MEAL]

    def _method_se_reposer(self, beliefs: "Beliefs", environment: "Environment") -> list:
        return [_SLEEP]

    def _method_se_detendre(self, beliefs: "Beliefs", environment: "Environment") -> list:
        return [_REST, _SOCIALIZE]

    def _method_default(self, beliefs: "Beliefs", environment: "Environment") -> list:
        return [_REST]
