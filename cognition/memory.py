"""Mémoire court terme et long terme (section 7)."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CycleRecord:
    day_index: int
    hour_of_day: float
    action_name: str
    desire_name: str
    success: bool
    fatigue: float
    hunger: float
    stress: float
    health: float


class ShortTermMemory:
    """Fenêtre glissante des N derniers cycles (section 7)."""

    def __init__(self, window: int = 48):
        self.window = window
        self._records: deque[CycleRecord] = deque(maxlen=window)

    def record(self, record: CycleRecord) -> None:
        self._records.append(record)

    def consecutive_insufficient_sleep_nights(self, fatigue_alert_threshold: float = 65.0) -> int:
        """Nombre de nuits consécutives récentes où l'action sleep.sleep s'est terminée
        avec une fatigue encore au-dessus du seuil d'alerte (sommeil insuffisant)."""
        count = 0
        for rec in reversed(self._records):
            if rec.action_name != "sleep.sleep":
                continue
            if rec.fatigue >= fatigue_alert_threshold:
                count += 1
            else:
                break
        return count

    def recent(self, n: int) -> list[CycleRecord]:
        return list(self._records)[-n:]


@dataclass
class ActionStats:
    successes: int = 0
    failures: int = 0
    moving_average: float = 0.5  # taux de succès lissé (moyenne mobile, section 7)


class LongTermMemory:
    """Compteurs succès/échec par type d'action, ajustés par moyenne mobile (section 7)."""

    def __init__(self, smoothing: float = 0.1):
        self.smoothing = smoothing
        self._stats: dict[str, ActionStats] = {}

    def record(self, action_name: str, success: bool) -> None:
        stats = self._stats.setdefault(action_name, ActionStats())
        if success:
            stats.successes += 1
        else:
            stats.failures += 1
        target = 1.0 if success else 0.0
        stats.moving_average += self.smoothing * (target - stats.moving_average)

    def success_rate(self, action_name: str) -> float:
        return self._stats.get(action_name, ActionStats()).moving_average

    def learning_bonus(self, action_name: str) -> float:
        """Petit ajustement de score reflétant l'expérience passée de cette action
        (moyenne mobile centrée sur 0.5 -> bonus/malus dans [-0.05, 0.05])."""
        return (self.success_rate(action_name) - 0.5) * 0.1

    def as_dict(self) -> dict[str, Any]:
        return {
            name: {"successes": s.successes, "failures": s.failures, "success_rate": round(s.moving_average, 3)}
            for name, s in self._stats.items()
        }
