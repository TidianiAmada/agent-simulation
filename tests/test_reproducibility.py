"""Tests de non-régression (section 17 : critères d'acceptation)."""
from __future__ import annotations

import pandas as pd

from config.schema import AgentProfile, RootConfig, SimulationConfig
from main import run_simulation


def _short_config(seed: int = 7, duration_days: int = 60) -> RootConfig:
    return RootConfig(
        simulation=SimulationConfig(duration_days=duration_days, seed=seed, output_dir="output_test"),
        agent=AgentProfile(),
    )


def test_same_seed_produces_identical_journal():
    config = _short_config()
    journal_a, events_a, exam_a = run_simulation(config)
    journal_b, events_b, exam_b = run_simulation(config)

    pd.testing.assert_frame_equal(journal_a, journal_b)
    pd.testing.assert_frame_equal(events_a, events_b)
    pd.testing.assert_frame_equal(exam_a, exam_b)


def test_different_seed_produces_different_journal():
    journal_a, _, _ = run_simulation(_short_config(seed=1))
    journal_b, _, _ = run_simulation(_short_config(seed=2))
    assert not journal_a["action"].equals(journal_b["action"])


def test_beliefs_stay_within_bounds():
    journal, _, _ = run_simulation(_short_config())
    for column in ("fatigue", "hunger", "stress", "health", "social"):
        assert journal[column].min() >= 0.0
        assert journal[column].max() <= 100.0
    assert journal["duration_hours"].min() > 0.0


def test_exactly_one_action_per_cycle():
    journal, _, _ = run_simulation(_short_config())
    assert journal["action"].notna().all()
    assert (journal["action"] != "").all()


def test_full_year_triggers_all_required_event_types():
    """Critère d'acceptation (section 17) : au moins un événement de chaque type
    (illness, exam, rent, inflation) doit survenir sur une année académique complète."""
    config = RootConfig(
        simulation=SimulationConfig(duration_days=270, seed=42, output_dir="output_test"),
        agent=AgentProfile(),
    )
    journal, events, exam_results = run_simulation(config)

    assert len(journal) > 0
    event_names = set(events["event"])
    for required in ("illness", "exam", "rent", "inflation"):
        assert required in event_names, f"événement requis absent du journal : {required}"
    assert len(exam_results) > 0
