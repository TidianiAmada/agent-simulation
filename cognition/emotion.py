"""Modèle émotionnel (section 8) : stress et moral, décroissance vers une baseline
et réaction aux croyances/événements/actions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from models.nta import Alert, AlertLevel

if TYPE_CHECKING:
    from actions.base import Action
    from agents.beliefs import Beliefs


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


@dataclass
class EmotionState:
    stress: float
    moral: float
    stress_baseline: float
    moral_baseline: float
    decay_rate: float

    def _decay_toward_baseline(self, dt_hours: float) -> None:
        step = self.decay_rate * dt_hours
        if self.stress > self.stress_baseline:
            self.stress = max(self.stress_baseline, self.stress - step)
        else:
            self.stress = min(self.stress_baseline, self.stress + step)
        if self.moral < self.moral_baseline:
            self.moral = min(self.moral_baseline, self.moral + step)
        else:
            self.moral = max(self.moral_baseline, self.moral - step)

    def update_from_state(self, beliefs: "Beliefs", alerts: list[Alert], dt_hours: float) -> None:
        """Décroissance naturelle + réaction aux croyances/alertes courantes (E_t = clamp(E_{t-1} + Δ - decay))."""
        self._decay_toward_baseline(dt_hours)

        for alert in alerts:
            bump = 6.0 if alert.level == AlertLevel.CRITICAL else 2.5
            self.stress += bump * (dt_hours / 1.0 if dt_hours < 1 else 1.0)

        if beliefs.days_to_next_exam <= 7 and any(
            p < 70 for p in beliefs.academic_progress.values()
        ):
            self.stress += 1.5

        if beliefs.days_to_rent_due <= 3 and beliefs.money < beliefs.rent_amount:
            self.stress += 3.0

        if beliefs.money < 0:
            self.stress += 4.0
            self.moral -= 2.0

        self.stress = _clamp(self.stress)
        self.moral = _clamp(self.moral)

    def apply_action_outcome(self, action: "Action", success: bool) -> None:
        if success:
            self.moral = _clamp(self.moral + action.base_satisfaction * 10.0)
        else:
            self.moral = _clamp(self.moral - 3.0)
            self.stress = _clamp(self.stress + 2.0)

    def apply_event_impact(self, stress_delta: float = 0.0, moral_delta: float = 0.0) -> None:
        self.stress = _clamp(self.stress + stress_delta)
        self.moral = _clamp(self.moral + moral_delta)

    def stress_weight_multiplier(self) -> float:
        """Pondération dynamique optionnelle (section 6) : un stress élevé augmente w_stress."""
        if self.stress >= 80:
            return 1.6
        if self.stress >= 60:
            return 1.25
        return 1.0
