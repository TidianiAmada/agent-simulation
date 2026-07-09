"""Agrégation du journal de simulation en un JSON compact pour le tableau de bord
(dashboard statique exporté en artefact, ou API de l'application Flask)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

CATEGORY_ORDER = ["travail", "etude", "sommeil", "loisir", "autre"]
CATEGORY_LABELS = {
    "travail": "Travail",
    "etude": "Étude",
    "sommeil": "Sommeil",
    "loisir": "Loisir",
    "autre": "Autre",
}
ACTION_LABELS = {
    "work.shift": "Travaille (service rémunéré)",
    "eat.budget_meal": "Mange (repas économique)",
    "eat.normal_meal": "Mange (repas normal)",
    "study.attend_course": "Assiste à un cours",
    "study.review": "Révise ses cours",
    "sleep.sleep": "Dort",
    "leisure.rest": "Se repose",
    "leisure.socialize": "Sort, retrouve des amis",
    "finance.request_family_help": "Sollicite l'aide de sa famille",
}
DESIRE_LABELS = {
    "reussir_examen": "Réussir l'examen",
    "payer_loyer": "Payer le loyer",
    "rester_en_bonne_sante": "Rester en bonne santé",
    "se_nourrir": "Se nourrir",
    "se_reposer": "Se reposer",
    "se_detendre": "Se détendre",
}
EVENT_LABELS = {
    "rent": "Loyer",
    "inflation": "Inflation",
    "exam": "Examen",
    "exam_surprise": "Examen surprise",
    "illness": "Maladie",
    "job_loss": "Perte d'emploi",
    "family_help": "Aide familiale",
}
EVENT_SEVERITY = {
    "rent": "neutral",  # requalifié paid/unpaid dans aggregate()
    "inflation": "warning",
    "exam": "neutral",  # requalifié passed/failed dans aggregate()
    "exam_surprise": "warning",
    "illness": "critical",
    "job_loss": "critical",
    "family_help": "good",
}


def aggregate(journal: pd.DataFrame, events: pd.DataFrame, exam_results: pd.DataFrame, summary: dict[str, Any]) -> dict[str, Any]:
    """Construit le payload du tableau de bord à partir des DataFrames en mémoire
    (utilisé aussi bien après une nouvelle exécution que pour rejouer un journal existant)."""
    subjects = sorted(c.replace("academic_", "") for c in journal.columns if c.startswith("academic_"))
    start_date = journal["datetime"].min().date()

    days = []
    max_day = int(journal["day_index"].max())
    for day_index in range(max_day + 1):
        rows = journal[journal["day_index"] == day_index]
        if rows.empty:
            continue
        last = rows.iloc[-1]
        hours = rows.groupby("category")["duration_hours"].sum().to_dict()
        days.append(
            {
                "d": day_index,
                "date": (start_date + pd.Timedelta(days=day_index)).isoformat(),
                "money": round(float(last["money"]), 1),
                "health": round(float(last["health"]), 1),
                "fatigue": round(float(last["fatigue"]), 1),
                "hunger": round(float(last["hunger"]), 1),
                "stress": round(float(last["stress"]), 1),
                "social": round(float(last["social"]), 1),
                "moral": round(float(last["moral"]), 1),
                "sleep_debt": round(float(last["sleep_debt"]), 2),
                "job_status": last["job_status"],
                "academic": {s: round(float(last[f"academic_{s}"]), 1) for s in subjects},
                "hours": {cat: round(float(hours.get(cat, 0.0)), 2) for cat in CATEGORY_ORDER},
                "action": last["action"],
                "action_label": ACTION_LABELS.get(last["action"], last["action"]),
                "desire": last["desire"] if isinstance(last["desire"], str) else None,
                "desire_label": DESIRE_LABELS.get(last["desire"], "") if isinstance(last["desire"], str) else "",
            }
        )

    events_out = []
    for _, row in events.iterrows():
        name = row["event"]
        severity = EVENT_SEVERITY.get(name, "warning")
        description = row["description"]
        if name == "rent":
            severity = "serious" if "impay" in description else "good"
        if name == "exam":
            severity = "good" if "réussi" in description else "critical"
        events_out.append(
            {
                "d": int(row["day_index"]),
                "event": name,
                "label": EVENT_LABELS.get(name, name),
                "description": description,
                "severity": severity,
            }
        )

    exams_out = []
    for _, row in exam_results.iterrows():
        exam_date = row["date"] if hasattr(row["date"], "year") else pd.Timestamp(row["date"])
        exam_date = exam_date.date() if hasattr(exam_date, "date") else exam_date
        exams_out.append(
            {
                "d": (exam_date - start_date).days,
                "subject": row["subject"],
                "date": exam_date.isoformat(),
                "score": round(float(row["score"]), 1),
                "passed": bool(row["passed"]),
            }
        )

    return {
        "meta": {
            "start_date": start_date.isoformat(),
            "end_date": days[-1]["date"] if days else start_date.isoformat(),
            "n_days": len(days),
            "subjects": subjects,
            "categories": [{"key": c, "label": CATEGORY_LABELS[c]} for c in CATEGORY_ORDER],
        },
        "days": days,
        "events": events_out,
        "exams": exams_out,
        "summary": summary,
    }


def build_from_output_dir(output_dir: Path | str) -> dict[str, Any]:
    """Reconstruit le payload à partir des fichiers exportés par `main.py` (CLI)."""
    output_dir = Path(output_dir)
    journal = pd.read_csv(output_dir / "journal.csv", parse_dates=["datetime"])
    events = pd.read_csv(output_dir / "events.csv", parse_dates=["datetime"])
    exam_results = pd.read_csv(output_dir / "exam_results.csv", parse_dates=["date"])
    with open(output_dir / "indicators.json", encoding="utf-8") as f:
        summary = json.load(f)
    return aggregate(journal, events, exam_results, summary)


def to_json_payload(data: dict[str, Any]) -> str:
    """Sérialise en JSON compact, avec échappement de `</` pour une insertion sûre dans un <script>."""
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return payload.replace("</", "<\\/")
