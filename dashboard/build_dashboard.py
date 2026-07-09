"""Reconstruit le tableau de bord statique autonome (dashboard/simulation_dashboard.html)
à partir des derniers résultats exportés dans output/ (voir main.py)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # ce script vit sous dashboard/, il faut la racine du projet pour les imports absolus

from statistics.dashboard_data import build_from_output_dir, to_json_payload

OUTPUT_DIR = ROOT / "output"
DASHBOARD_DIR = Path(__file__).resolve().parent


def main() -> None:
    data = build_from_output_dir(OUTPUT_DIR)
    template = (DASHBOARD_DIR / "template.html").read_text(encoding="utf-8")
    if "__SIMULATION_DATA__" not in template:
        raise RuntimeError("Placeholder __SIMULATION_DATA__ introuvable dans template.html")
    output_html = template.replace("__SIMULATION_DATA__", to_json_payload(data))
    out_path = DASHBOARD_DIR / "simulation_dashboard.html"
    out_path.write_text(output_html, encoding="utf-8")
    print(f"Ecrit : {out_path} ({out_path.stat().st_size / 1024:.0f} Ko, {len(data['days'])} jours)")


if __name__ == "__main__":
    main()
