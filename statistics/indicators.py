"""Calcul des indicateurs agrégés (KPIs) à partir du journal de simulation (section 13)."""
from __future__ import annotations

from typing import Any

import pandas as pd
from scipy import stats as scipy_stats


def academic_progress_columns(journal: pd.DataFrame) -> list[str]:
    return [c for c in journal.columns if c.startswith("academic_")]


def time_allocation(journal: pd.DataFrame) -> pd.Series:
    """Répartition du temps (heures) par catégorie d'action."""
    return journal.groupby("category")["duration_hours"].sum().sort_values(ascending=False)


def exam_success_rate(exam_results: pd.DataFrame) -> float:
    if exam_results.empty:
        return float("nan")
    return float(exam_results["passed"].mean())


def days_in_financial_distress(journal: pd.DataFrame, threshold: float = 0.0) -> int:
    daily_last = journal.sort_values("datetime").groupby("day_index")["money"].last()
    return int((daily_last < threshold).sum())


def illness_episode_count(events: pd.DataFrame) -> int:
    if events.empty:
        return 0
    return int((events["event"] == "illness").sum())


def stress_vs_academic_correlation(journal: pd.DataFrame) -> float:
    academic_cols = academic_progress_columns(journal)
    if not academic_cols:
        return float("nan")
    daily = journal.groupby("day_index").agg(stress=("stress", "mean"), **{c: (c, "mean") for c in academic_cols})
    daily["academic_mean"] = daily[academic_cols].mean(axis=1)
    if daily["academic_mean"].std() == 0 or daily["stress"].std() == 0:
        return float("nan")
    corr, _ = scipy_stats.pearsonr(daily["stress"], daily["academic_mean"])
    return float(corr)


def summarize(journal: pd.DataFrame, events: pd.DataFrame, exam_results: pd.DataFrame) -> dict[str, Any]:
    academic_cols = academic_progress_columns(journal)
    final_row = journal.sort_values("datetime").iloc[-1]

    return {
        "n_cycles": len(journal),
        "simulated_days": int(journal["day_index"].max()) + 1 if not journal.empty else 0,
        "final_money": float(final_row["money"]),
        "min_money": float(journal["money"].min()),
        "final_health": float(final_row["health"]),
        "final_moral": float(final_row["moral"]),
        "mean_stress": float(journal["stress"].mean()),
        "mean_fatigue": float(journal["fatigue"].mean()),
        "final_academic_progress": {c.replace("academic_", ""): float(final_row[c]) for c in academic_cols},
        "exam_success_rate": exam_success_rate(exam_results),
        "n_exams": int(len(exam_results)),
        "days_financial_distress": days_in_financial_distress(journal),
        "n_illness_episodes": illness_episode_count(events),
        "time_allocation_hours": time_allocation(journal).to_dict(),
        "stress_vs_academic_correlation": stress_vs_academic_correlation(journal),
        "event_counts": events["event"].value_counts().to_dict() if not events.empty else {},
    }
