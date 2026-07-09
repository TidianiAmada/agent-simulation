"""Modèle Besoins-Seuils-Alertes (Needs/Thresholds/Alerts, section 9).

Les 5 besoins fondamentaux (faim, sommeil/fatigue, santé, lien social, finances)
correspondent directement à des champs de `Beliefs` (section 3.1). Le NTA ne
duplique donc pas cet état : il applique la dégradation naturelle par cycle et
calcule les niveaux d'alerte à partir des valeurs courantes des croyances,
qui restent l'unique source de vérité (les actions/événements modifient les
croyances, jamais le NTA directement).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from config.schema import NeedThresholds, NTAConfig

if TYPE_CHECKING:
    from agents.beliefs import Beliefs

# Besoins pour lesquels une valeur élevée est défavorable (faim, fatigue, isolement social).
# Le stress et le moral ne sont PAS des besoins NTA : ils relèvent du modèle émotionnel (section 8).
HIGHER_IS_WORSE = {"hunger", "fatigue", "social"}
LOWER_IS_WORSE = {"health", "finances"}

# Nom du besoin NTA -> nom du champ correspondant dans Beliefs.
NEED_TO_BELIEF_FIELD = {
    "hunger": "hunger",
    "fatigue": "fatigue",
    "health": "health",
    "social": "social",
    "finances": "money",
}


class AlertLevel(str, Enum):
    COMFORT = "comfort"
    ALERT = "alert"
    CRITICAL = "critical"


@dataclass
class Alert:
    need_name: str
    level: AlertLevel
    value: float


class NeedsSystem:
    def __init__(self, nta: NTAConfig):
        self.thresholds: dict[str, NeedThresholds] = {
            "hunger": nta.hunger,
            "fatigue": nta.fatigue,
            "health": nta.health,
            "social": nta.social,
            "finances": nta.finances,
        }

    def degrade_all(self, beliefs: "Beliefs", dt_hours: float, exclude: tuple[str, ...] = ("finances",)) -> None:
        """Applique la dégradation naturelle par heure aux champs de `beliefs`."""
        for name, thresholds in self.thresholds.items():
            if name in exclude:
                continue
            field = NEED_TO_BELIEF_FIELD[name]
            delta = thresholds.degradation_per_hour * dt_hours
            current = getattr(beliefs, field)
            new_value = current + delta if name in HIGHER_IS_WORSE else current - delta
            if field != "money":
                new_value = max(0.0, min(100.0, new_value))
            setattr(beliefs, field, new_value)

    def alert_level(self, name: str, value: float) -> AlertLevel:
        t = self.thresholds[name]
        if name in HIGHER_IS_WORSE:
            if value >= t.critical:
                return AlertLevel.CRITICAL
            if value >= t.alert:
                return AlertLevel.ALERT
            return AlertLevel.COMFORT
        else:
            if value <= t.critical:
                return AlertLevel.CRITICAL
            if value <= t.alert:
                return AlertLevel.ALERT
            return AlertLevel.COMFORT

    def alerts(self, beliefs: "Beliefs") -> list[Alert]:
        result = []
        for name, field in NEED_TO_BELIEF_FIELD.items():
            value = getattr(beliefs, field)
            level = self.alert_level(name, value)
            if level != AlertLevel.COMFORT:
                result.append(Alert(need_name=name, level=level, value=value))
        return result
