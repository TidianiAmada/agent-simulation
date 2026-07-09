"""Classe `Student` : assemble beliefs/desires/intentions/mémoire/émotions et exécute
le cycle cognitif (section 4)."""
from __future__ import annotations

from typing import Any

import numpy as np

from actions import ALL_ACTIONS
from actions.sleep import Sleep
from agents.beliefs import Beliefs
from agents.desires import dominant_desire, generate_desires
from agents.intentions import IntentionStack, needs_replanning
from agents.planner import HTNPlanner
from cognition.decision import DecisionResult, select_action
from cognition.emotion import EmotionState
from cognition.memory import CycleRecord, LongTermMemory, ShortTermMemory
from config.schema import AgentProfile
from core.environment import Environment
from models.nta import NeedsSystem

_SLEEP_FALLBACK = Sleep()


def _outcome_success(action_name: str, delta) -> bool:
    if action_name.startswith("sleep"):
        return delta.fatigue < 0
    if action_name.startswith("eat"):
        return delta.hunger < 0
    if action_name.startswith("work"):
        return delta.money > 0
    if action_name.startswith("study"):
        return bool(delta.academic_progress) and any(v > 0 for v in delta.academic_progress.values())
    if action_name.startswith("leisure"):
        return delta.stress < 0
    if action_name.startswith("finance"):
        return delta.money > 0
    return True


class Student:
    def __init__(self, profile: AgentProfile, rng: np.random.Generator, start_datetime):
        self.profile = profile
        self.rng = rng

        self.beliefs = Beliefs(
            money=profile.initial_money,
            fatigue=profile.initial_fatigue,
            hunger=profile.initial_hunger,
            stress=profile.initial_stress,
            social=50.0,
            health=profile.initial_health,
            sleep_debt=profile.initial_sleep_debt,
            academic_progress={s: profile.initial_academic_progress for s in profile.subjects},
            job_status=profile.job_status,
            current_datetime=start_datetime,
        )
        self.emotion = EmotionState(
            stress=profile.initial_stress,
            moral=profile.emotion_moral_baseline,
            stress_baseline=profile.emotion_stress_baseline,
            moral_baseline=profile.emotion_moral_baseline,
            decay_rate=profile.emotion_decay_rate,
        )
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory()
        self.intentions = IntentionStack()
        self.planner = HTNPlanner(profile.nta)
        self.needs_system = NeedsSystem(profile.nta)
        self.force_replan = False
        self.exam_results: list[dict[str, Any]] = []

    def notify_significant_event(self) -> None:
        """Appelée par le moteur d'événements quand une intention doit être abandonnée (section 3.3)."""
        self.force_replan = True

    def step(self, environment: Environment, day_index: int, dt_hours: float) -> dict[str, Any]:
        # 1. Perception
        perception = environment.perceive()

        # 2. Mise à jour des croyances (perception + dégradation naturelle des besoins NTA)
        self.beliefs.sync_from_perception(perception)
        self.needs_system.degrade_all(self.beliefs, dt_hours)
        alerts = self.needs_system.alerts(self.beliefs)

        # 3. Mise à jour des émotions (décroissance + réaction aux croyances/alertes)
        self.emotion.update_from_state(self.beliefs, alerts, dt_hours)
        self.beliefs.sync_stress(self.emotion.stress)

        # 4. Génération des désirs
        desires = generate_desires(self.beliefs, self.emotion, self.profile.nta)
        dominant = dominant_desire(desires)

        # 5. Planification (seulement si nécessaire)
        if needs_replanning(
            self.intentions.current,
            dominant,
            self.beliefs,
            environment,
            self.profile.replanning_priority_threshold,
            self.force_replan,
        ):
            intention = self.planner.decompose(dominant, self.beliefs, environment, day_index)
            self.intentions.replace_current(intention)
            self.force_replan = False

        # 6. Choix de l'action parmi les options du plan courant
        intention = self.intentions.current
        candidates = intention.plan if (intention and intention.plan) else ALL_ACTIONS
        weights = self.profile.utility_weights.as_dict()
        decision = select_action(
            candidates,
            self.beliefs,
            environment,
            self.emotion,
            weights,
            self.profile.exploration_epsilon,
            self.profile.dynamic_weights_enabled,
            self.rng,
            self.long_term_memory,
        )
        if decision is None:
            decision = select_action(
                ALL_ACTIONS,
                self.beliefs,
                environment,
                self.emotion,
                weights,
                self.profile.exploration_epsilon,
                self.profile.dynamic_weights_enabled,
                self.rng,
                self.long_term_memory,
            )
        if decision is None:
            # Filet de sécurité (ne devrait jamais se produire : eat/sleep n'ont quasiment pas
            # de préconditions bloquantes) : on force un repos minimal pour ne pas planter.
            duration = _SLEEP_FALLBACK.pick_duration(self.rng)
            decision = DecisionResult(action=_SLEEP_FALLBACK, utility=0.0, criteria={}, weights_used=weights)
        else:
            duration = decision.action.pick_duration(self.rng)

        action = decision.action

        # 7. Exécution
        delta = action.apply(self.beliefs, environment, duration, self.rng)
        self.beliefs.apply_delta(delta, duration)
        self.emotion.apply_event_impact(stress_delta=delta.stress)
        if intention is not None:
            intention.consume(action)
        success = _outcome_success(action.name, delta)
        self.emotion.apply_action_outcome(action, success)
        self.beliefs.sync_stress(self.emotion.stress)

        # 8. Apprentissage simple
        self.long_term_memory.record(action.name, success)
        self.short_term_memory.record(
            CycleRecord(
                day_index=day_index,
                hour_of_day=perception.hour_of_day,
                action_name=action.name,
                desire_name=dominant.name if dominant else "",
                success=success,
                fatigue=self.beliefs.fatigue,
                hunger=self.beliefs.hunger,
                stress=self.beliefs.stress,
                health=self.beliefs.health,
            )
        )

        # 9. Le journal détaillé est assemblé ici et collecté par le scheduler (statistics/indicators.py)
        record: dict[str, Any] = {
            "datetime": perception.current_datetime,
            "day_index": day_index,
            "hour_of_day": perception.hour_of_day,
            "weekday": perception.weekday,
            "period": perception.period.value,
            "action": action.name,
            "category": action.category.value,
            "duration_hours": duration,
            "desire": dominant.name if dominant else None,
            "desire_intensity": dominant.intensity if dominant else 0.0,
            "utility": decision.utility,
            "success": success,
            "money": self.beliefs.money,
            "health": self.beliefs.health,
            "fatigue": self.beliefs.fatigue,
            "hunger": self.beliefs.hunger,
            "stress": self.beliefs.stress,
            "social": self.beliefs.social,
            "moral": self.emotion.moral,
            "sleep_debt": self.beliefs.sleep_debt,
            "job_status": self.beliefs.job_status.value,
        }
        for subject, progress in self.beliefs.academic_progress.items():
            record[f"academic_{subject}"] = progress

        return record, duration
