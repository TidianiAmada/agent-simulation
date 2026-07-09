"""Traduit l'état des besoins/croyances en intensité de désirs (section 3.2)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from config.schema import NTAConfig

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from cognition.emotion import EmotionState

DESIRE_NAMES = (
    "reussir_examen",
    "payer_loyer",
    "rester_en_bonne_sante",
    "se_nourrir",
    "se_reposer",
    "se_detendre",
)


def _ramp(value: float, low: float, high: float) -> float:
    if high <= low:
        return 1.0 if value >= high else 0.0
    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return (value - low) / (high - low)


def compute_intensities(beliefs: "Beliefs", emotion: "EmotionState", nta: NTAConfig) -> dict[str, float]:
    intensities: dict[str, float] = {}

    intensities["se_nourrir"] = _ramp(beliefs.hunger, nta.hunger.comfort, nta.hunger.critical)
    intensities["se_reposer"] = _ramp(beliefs.sleep_debt, 2.0, 12.0)

    health_component = _ramp(100 - beliefs.health, 100 - nta.health.comfort, 100 - nta.health.critical)
    fatigue_component = _ramp(beliefs.fatigue, nta.fatigue.comfort, nta.fatigue.critical)
    stress_component = _ramp(emotion.stress, 40.0, 90.0)
    intensities["rester_en_bonne_sante"] = max(health_component, 0.6 * fatigue_component, 0.4 * stress_component)

    if beliefs.days_to_next_exam != float("inf"):
        urgency = _ramp(30 - beliefs.days_to_next_exam, 0, 30)
        avg_progress = (
            sum(beliefs.academic_progress.values()) / len(beliefs.academic_progress)
            if beliefs.academic_progress
            else 100.0
        )
        deficit = _ramp(100 - avg_progress, 20, 90)
        intensities["reussir_examen"] = 0.5 * urgency + 0.5 * deficit
    else:
        intensities["reussir_examen"] = 0.1

    if beliefs.days_to_rent_due != float("inf"):
        shortfall = max(0.0, beliefs.rent_amount - beliefs.money)
        shortfall_ratio = _ramp(shortfall, 0, max(beliefs.rent_amount, 1.0))
        urgency = _ramp(15 - beliefs.days_to_rent_due, 0, 15)
        intensities["payer_loyer"] = max(shortfall_ratio, urgency) if shortfall > 0 else 0.1 * urgency
    else:
        intensities["payer_loyer"] = 0.0

    urgent_other = max(intensities.get("reussir_examen", 0.0), intensities.get("payer_loyer", 0.0)) > 0.6
    base_relax = _ramp(emotion.stress, 40.0, 90.0)
    intensities["se_detendre"] = base_relax * (0.4 if urgent_other else 1.0)
    if emotion.stress >= 85.0:
        # Un stress très élevé augmente l'intensité du désir "se détendre" (section 8),
        # même en présence d'une urgence académique/financière concurrente.
        intensities["se_detendre"] = max(intensities["se_detendre"], 0.9)

    return {k: max(0.0, min(1.0, v)) for k, v in intensities.items()}
