"""Interface commune des actions primitives (section 10)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

from agents.beliefs import BeliefsDelta

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from core.environment import Environment


class ActionCategory(str, Enum):
    WORK = "travail"
    STUDY = "etude"
    SLEEP = "sommeil"
    LEISURE = "loisir"
    OTHER = "autre"


class Action(ABC):
    name: str
    category: ActionCategory
    min_duration: float
    max_duration: float

    @property
    def expected_duration(self) -> float:
        return (self.min_duration + self.max_duration) / 2.0

    def pick_duration(self, rng: np.random.Generator) -> float:
        if self.min_duration == self.max_duration:
            return self.min_duration
        return float(rng.uniform(self.min_duration, self.max_duration))

    @abstractmethod
    def preconditions(self, beliefs: "Beliefs", environment: "Environment") -> bool:
        ...

    @abstractmethod
    def effects(self, beliefs: "Beliefs", environment: "Environment", duration: float) -> BeliefsDelta:
        """Delta *attendu* (valeur espérée) pour une durée donnée : utilisé par
        `cognition/utility.py` pour noter l'action sans dépendre d'un tirage aléatoire."""
        ...

    def apply(self, beliefs: "Beliefs", environment: "Environment", duration: float, rng: np.random.Generator) -> BeliefsDelta:
        """Delta réellement appliqué à l'exécution. Par défaut identique à `effects`
        (déterministe) ; les actions à issue probabiliste (ex. aide familiale) surchargent
        cette méthode pour tirer un résultat au sort tout en gardant `effects` déterministe
        pour l'estimation d'utilité."""
        return self.effects(beliefs, environment, duration)

    def cost(self, beliefs: "Beliefs", environment: "Environment") -> float:
        return 0.0
