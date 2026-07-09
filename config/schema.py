"""Schémas Pydantic de configuration (section 14 des spécifications)."""
from __future__ import annotations

import datetime as dt
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class JobStatus(str, Enum):
    EMPLOYED = "employed"
    UNEMPLOYED = "unemployed"


class UtilityWeights(BaseModel):
    """Poids w_i de la fonction d'utilité U(a) (section 6). Doivent sommer à 1."""

    academic: float = 0.25
    financial: float = 0.20
    fatigue: float = 0.15
    stress: float = 0.15
    hunger: float = 0.15
    satisfaction: float = 0.10

    @model_validator(mode="after")
    def _weights_sum_to_one(self) -> "UtilityWeights":
        total = self.academic + self.financial + self.fatigue + self.stress + self.hunger + self.satisfaction
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Les poids de la fonction d'utilité doivent sommer à 1.0 (actuel: {total})")
        return self

    def as_dict(self) -> dict[str, float]:
        return {
            "academic": self.academic,
            "financial": self.financial,
            "fatigue": self.fatigue,
            "stress": self.stress,
            "hunger": self.hunger,
            "satisfaction": self.satisfaction,
        }


class NeedThresholds(BaseModel):
    """Seuils confort/alerte/critique pour un besoin NTA (section 9)."""

    comfort: float
    alert: float
    critical: float
    degradation_per_hour: float


class NTAConfig(BaseModel):
    """Seuils des 5 besoins fondamentaux (section 9). Le stress et le moral relèvent
    exclusivement du modèle émotionnel (section 8), pas du NTA."""

    hunger: NeedThresholds = NeedThresholds(comfort=30, alert=60, critical=85, degradation_per_hour=2.0)
    fatigue: NeedThresholds = NeedThresholds(comfort=40, alert=65, critical=90, degradation_per_hour=1.5)
    health: NeedThresholds = NeedThresholds(comfort=60, alert=35, critical=15, degradation_per_hour=0.05)
    social: NeedThresholds = NeedThresholds(comfort=40, alert=70, critical=90, degradation_per_hour=0.3)
    finances: NeedThresholds = NeedThresholds(comfort=20000, alert=5000, critical=0, degradation_per_hour=0.0)


class AgentProfile(BaseModel):
    """État initial et paramètres propres à l'agent étudiant."""

    name: str = "etudiant"
    subjects: list[str] = Field(default_factory=lambda: ["Mathematiques", "Algorithmique", "Anglais"])

    initial_money: float = 75000.0
    initial_health: float = 80.0
    initial_fatigue: float = 25.0
    initial_hunger: float = 25.0
    initial_stress: float = 30.0
    initial_sleep_debt: float = 0.0
    initial_academic_progress: float = 5.0
    job_status: JobStatus = JobStatus.EMPLOYED

    utility_weights: UtilityWeights = Field(default_factory=UtilityWeights)
    nta: NTAConfig = Field(default_factory=NTAConfig)

    emotion_stress_baseline: float = 30.0
    emotion_moral_baseline: float = 60.0
    emotion_decay_rate: float = 3.0

    exploration_epsilon: float = 0.02
    dynamic_weights_enabled: bool = True

    salary_per_shift: float = 8000.0
    rent_amount: float = 45000.0
    meal_cost_budget: float = 1000.0
    meal_cost_normal: float = 2500.0

    replanning_priority_threshold: float = 0.75


class SimulationConfig(BaseModel):
    """Paramètres globaux de la simulation."""

    start_date: dt.date = dt.date(2025, 9, 1)
    duration_days: int = 270
    time_step_hours: float = 1.0
    seed: int = 42
    output_dir: str = "output"

    illness_base_probability_per_hour: float = 0.0006
    exam_surprise_probability_per_hour: float = 0.0004
    inflation_period_days: int = 30
    inflation_rate_mean: float = 0.01
    inflation_rate_std: float = 0.004
    rent_due_day_of_month: int = 5
    job_loss_probability_per_hour: float = 0.00006
    family_help_probability_per_hour: float = 0.0003

    @field_validator("duration_days")
    @classmethod
    def _positive_duration(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("duration_days doit être positif")
        return v


class RootConfig(BaseModel):
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    agent: AgentProfile = Field(default_factory=AgentProfile)
