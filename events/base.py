"""Interface commune du moteur d'événements (section 11)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.student import Student
    from core.environment import Environment


@dataclass
class EventOccurrence:
    name: str
    description: str
    day_index: int


class Event(ABC):
    name: str

    @abstractmethod
    def check_and_apply(self, environment: "Environment", student: "Student", dt_hours: float) -> EventOccurrence | None:
        """Vérifie si l'événement se déclenche sur l'intervalle [t, t+dt_hours) et, le cas
        échéant, modifie `environment` et/ou les croyances de `student` puis retourne une
        `EventOccurrence` pour le journal. Retourne `None` si rien ne se déclenche."""
        ...

    @staticmethod
    def _interval_probability(p_per_hour: float, dt_hours: float) -> float:
        """Probabilité composée qu'un événement de taux horaire `p_per_hour` survienne
        au moins une fois durant un intervalle de `dt_hours` heures."""
        return 1.0 - (1.0 - p_per_hour) ** dt_hours
