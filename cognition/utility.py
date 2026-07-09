"""Fonction d'utilité U(a) = Σ w_i · f_i(a) (section 6)."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from cognition.emotion import EmotionState

if TYPE_CHECKING:
    from actions.base import Action
    from agents.beliefs import Beliefs
    from core.environment import Environment

FINANCIAL_SCALE = 20000.0  # ordre de grandeur d'une dépense/recette significative (référence: le loyer)


def _clip01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _relief_score(delta: float, current: float, scale: float) -> float:
    """[0,1] : 0.5 = neutre ; >0.5 si l'action réduit `current` (delta<0), <0.5 si elle l'aggrave.
    L'effet est amplifié par la sévérité courante du besoin (pénalise davantage si déjà élevé)."""
    severity = _clip01(current / 100.0)
    raw = 0.5 - (delta / scale) * (0.5 + 0.5 * severity)
    return _clip01(raw)


def compute_weights(base_weights: dict[str, float], emotion: EmotionState, dynamic_enabled: bool) -> dict[str, float]:
    if not dynamic_enabled:
        return dict(base_weights)
    weights = dict(base_weights)
    weights["stress"] *= emotion.stress_weight_multiplier()
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def compute_utility(
    action: "Action",
    beliefs: "Beliefs",
    environment: "Environment",
    emotion: EmotionState,
    weights: dict[str, float],
    epsilon: float,
    rng: np.random.Generator,
) -> tuple[float, dict[str, float]]:
    delta = action.effects(beliefs, environment, action.expected_duration)

    f_academic = _clip01(sum(delta.academic_progress.values()) / 15.0) if delta.academic_progress else 0.0
    f_financial = _clip01(0.5 + delta.money / (2 * FINANCIAL_SCALE))
    f_fatigue = _relief_score(delta.fatigue, beliefs.fatigue, 40.0)
    f_stress = _relief_score(delta.stress, beliefs.stress, 30.0)
    f_hunger = _relief_score(delta.hunger, beliefs.hunger, 50.0)
    f_satisfaction = _clip01(action.base_satisfaction)

    criteria = {
        "academic": f_academic,
        "financial": f_financial,
        "fatigue": f_fatigue,
        "stress": f_stress,
        "hunger": f_hunger,
        "satisfaction": f_satisfaction,
    }
    base_utility = sum(weights[k] * v for k, v in criteria.items())
    noise = float(rng.uniform(-epsilon, epsilon))
    return base_utility + noise, criteria
