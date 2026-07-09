"""Application Flask exposant le tableau de bord de la simulation.

Sert l'interface (templates/index.html) et une petite API :
  GET  /api/config  -> valeurs par défaut (graine, durée) pour préremplir le panneau
  GET  /api/data    -> dernier résultat exporté dans output/ (lance une simulation
                       par défaut si aucun résultat n'existe encore)
  POST /api/run     -> exécute une nouvelle simulation avec les paramètres fournis
                       (graine, durée) et renvoie le payload agrégé du tableau de bord
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # ce module vit sous webapp/, il faut la racine du projet pour les imports absolus

from flask import Flask, jsonify, render_template, request
from pydantic import ValidationError

from config.schema import AgentProfile, RootConfig, SimulationConfig
from core.scheduler import Scheduler
from statistics import indicators as indicators_module
from statistics.dashboard_data import aggregate, build_from_output_dir

OUTPUT_DIR = ROOT / "output"
MAX_DURATION_DAYS = 400

app = Flask(__name__)


def run_and_export(seed: int, duration_days: int) -> dict:
    """Exécute une simulation complète, exporte les résultats dans output/ (CSV,
    graphiques, indicateurs — cohérent avec `main.py`) et renvoie le payload du
    tableau de bord construit directement depuis les DataFrames en mémoire."""
    config = RootConfig(
        simulation=SimulationConfig(seed=seed, duration_days=duration_days, output_dir=str(OUTPUT_DIR)),
        agent=AgentProfile(),
    )
    scheduler = Scheduler(config.simulation, config.agent)
    journal = scheduler.run()
    events = scheduler.events_dataframe()
    exam_results = scheduler.exam_results_dataframe()
    summary = indicators_module.summarize(journal, events, exam_results)

    from main import export_results  # import tardif : évite l'exécution du bloc __main__ de main.py

    export_results(config, journal, events, exam_results)
    return aggregate(journal, events, exam_results, summary)


@app.route("/")
def index():
    default_config = SimulationConfig()
    return render_template(
        "index.html",
        default_seed=default_config.seed,
        default_duration=default_config.duration_days,
        max_duration=MAX_DURATION_DAYS,
    )


@app.route("/api/config")
def api_config():
    default_config = SimulationConfig()
    return jsonify({"seed": default_config.seed, "duration_days": default_config.duration_days, "max_duration_days": MAX_DURATION_DAYS})


@app.route("/api/data")
def api_data():
    if not (OUTPUT_DIR / "journal.csv").exists():
        default_config = SimulationConfig()
        data = run_and_export(default_config.seed, default_config.duration_days)
        return jsonify(data)
    return jsonify(build_from_output_dir(OUTPUT_DIR))


@app.route("/api/run", methods=["POST"])
def api_run():
    body = request.get_json(silent=True) or {}
    try:
        seed = int(body.get("seed", 42))
        duration_days = int(body.get("duration_days", 270))
    except (TypeError, ValueError):
        return jsonify({"error": "La graine et la durée doivent être des nombres entiers."}), 400

    if not (1 <= duration_days <= MAX_DURATION_DAYS):
        return jsonify({"error": f"La durée doit être comprise entre 1 et {MAX_DURATION_DAYS} jours."}), 400
    if not (0 <= seed <= 2**31 - 1):
        return jsonify({"error": "La graine doit être un entier positif."}), 400

    try:
        data = run_and_export(seed, duration_days)
    except ValidationError as exc:
        return jsonify({"error": f"Configuration invalide : {exc}"}), 400
    except Exception as exc:  # garde-fou : une simulation ne devrait jamais planter le serveur
        return jsonify({"error": f"Échec de la simulation : {exc}"}), 500

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
