"""Sélection de l'action à exécuter parmi les options du plan courant (section 6)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from cognition.utility import compute_utility, compute_weights

if TYPE_CHECKING:
    from actions.base import Action
    from agents.beliefs import Beliefs
    from cognition.emotion import EmotionState
    from cognition.memory import LongTermMemory
    from core.environment import Environment


@dataclass
class DecisionResult:
    action: "Action"
    utility: float
    criteria: dict[str, float]
    weights_used: dict[str, float]


def select_action(
    candidates: list["Action"],
    beliefs: "Beliefs",
    environment: "Environment",
    emotion: "EmotionState",
    base_weights: dict[str, float],
    epsilon: float,
    dynamic_weights_enabled: bool,
    rng: np.random.Generator,
    long_term_memory: "LongTermMemory | None" = None,
) -> DecisionResult | None:
    feasible = [a for a in candidates if a.preconditions(beliefs, environment)]
    if not feasible:
        return None

    weights = compute_weights(base_weights, emotion, dynamic_weights_enabled)

    best: DecisionResult | None = None
    for action in feasible:
        utility, criteria = compute_utility(action, beliefs, environment, emotion, weights, epsilon, rng)
        if long_term_memory is not None:
            utility += long_term_memory.learning_bonus(action.name)
        if best is None or utility > best.utility:
            best = DecisionResult(action=action, utility=utility, criteria=criteria, weights_used=weights)
    return best
