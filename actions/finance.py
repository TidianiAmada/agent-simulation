"""Action de recours à l'aide familiale (méthode HTN "solliciter aide familiale", section 5.2).

Distincte de l'événement bonus `events/family_help.py` : ici l'agent sollicite
délibérément sa famille (déclenché par le planificateur quand le loyer est dû
et insolvable), avec une probabilité de succès, alors que l'événement bonus
survient spontanément sans initiative de l'agent.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from actions.base import Action, ActionCategory
from agents.beliefs import BeliefsDelta

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from core.environment import Environment


class RequestFamilyHelp(Action):
    name = "finance.request_family_help"
    category = ActionCategory.OTHER
    min_duration = 0.5
    max_duration = 0.5
    base_satisfaction = -0.1  # solliciter de l'aide est un soulagement financier mais coûte en fierté
    success_probability = 0.6
    help_amount = 30000.0

    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        return not beliefs.incapacitated

    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        # Valeur espérée utilisée pour le scoring d'utilité.
        return BeliefsDelta(
            money=self.success_probability * self.help_amount,
            stress=-self.success_probability * 6.0 + (1 - self.success_probability) * 2.0,
        )

    def apply(self, beliefs: "Beliefs", environment: "Environment", duration: float, rng: np.random.Generator) -> BeliefsDelta:
        if rng.random() < self.success_probability:
            return BeliefsDelta(money=self.help_amount, stress=-6.0)
        return BeliefsDelta(stress=2.0)
