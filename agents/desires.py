"""Génération et priorisation des désirs (section 3.2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from cognition.motivation import compute_intensities
from config.schema import NTAConfig

if TYPE_CHECKING:
    from agents.beliefs import Beliefs
    from cognition.emotion import EmotionState

DESIRE_LABELS = {
    "reussir_examen": "Réussir l'examen",
    "payer_loyer": "Payer le loyer",
    "rester_en_bonne_sante": "Rester en bonne santé",
    "se_nourrir": "Se nourrir",
    "se_reposer": "Se reposer",
    "se_detendre": "Se détendre",
}


@dataclass
class Desire:
    name: str
    intensity: float

    @property
    def label(self) -> str:
        return DESIRE_LABELS.get(self.name, self.name)


def generate_desires(beliefs: "Beliefs", emotion: "EmotionState", nta: NTAConfig) -> list[Desire]:
    intensities = compute_intensities(beliefs, emotion, nta)
    desires = [Desire(name=name, intensity=intensity) for name, intensity in intensities.items()]
    desires.sort(key=lambda d: d.intensity, reverse=True)
    return desires


def dominant_desire(desires: list[Desire]) -> Desire | None:
    return desires[0] if desires else None
