"""Point d'entrée : charge la config, instancie l'environnement et l'agent,
lance le scheduler, exporte les résultats (section 2 / main.py)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from config.schema import RootConfig
from core.scheduler import Scheduler
from statistics import indicators
from statistics.plots import generate_all_plots


def load_config(path: str | None) -> RootConfig:
    if path is None:
        return RootConfig()
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return RootConfig.model_validate(raw)


def run_simulation(config: RootConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scheduler = Scheduler(config.simulation, config.agent)
    journal = scheduler.run()
    events = scheduler.events_dataframe()
    exam_results = scheduler.exam_results_dataframe()
    return journal, events, exam_results


def export_results(config: RootConfig, journal: pd.DataFrame, events: pd.DataFrame, exam_results: pd.DataFrame) -> dict:
    output_dir = Path(config.simulation.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    journal.to_csv(output_dir / "journal.csv", index=False)
    events.to_csv(output_dir / "events.csv", index=False)
    exam_results.to_csv(output_dir / "exam_results.csv", index=False)

    summary = indicators.summarize(journal, events, exam_results)
    with open(output_dir / "indicators.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    generate_all_plots(journal, exam_results, str(output_dir))
    return summary


def print_summary(summary: dict) -> None:
    print("=" * 60)
    print("Résumé de la simulation")
    print("=" * 60)
    print(f"Cycles simulés          : {summary['n_cycles']}")
    print(f"Jours simulés           : {summary['simulated_days']}")
    print(f"Argent final            : {summary['final_money']:.0f} FCFA (min: {summary['min_money']:.0f})")
    print(f"Santé finale            : {summary['final_health']:.1f}")
    print(f"Moral final             : {summary['final_moral']:.1f}")
    print(f"Stress moyen            : {summary['mean_stress']:.1f}")
    print(f"Fatigue moyenne         : {summary['mean_fatigue']:.1f}")
    print(f"Progression académique  : {summary['final_academic_progress']}")
    print(f"Taux de réussite examens: {summary['exam_success_rate']}")
    print(f"Nb examens              : {summary['n_exams']}")
    print(f"Jours en détresse fin.  : {summary['days_financial_distress']}")
    print(f"Épisodes de maladie     : {summary['n_illness_episodes']}")
    print(f"Répartition du temps (h): {summary['time_allocation_hours']}")
    print(f"Corr. stress/académique : {summary['stress_vs_academic_correlation']}")
    print(f"Occurrences d'événements: {summary['event_counts']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulation d'un étudiant autonome (MVP)")
    parser.add_argument("--config", type=str, default="config/default.yaml", help="Chemin du fichier de configuration YAML")
    args = parser.parse_args()

    config_path = args.config if Path(args.config).exists() else None
    config = load_config(config_path)

    journal, events, exam_results = run_simulation(config)
    summary = export_results(config, journal, events, exam_results)
    print_summary(summary)
    print(f"\nRésultats exportés dans : {Path(config.simulation.output_dir).resolve()}")


if __name__ == "__main__":
    main()
