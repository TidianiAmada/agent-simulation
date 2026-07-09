"""Génération des graphiques (section 13)."""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from statistics.indicators import academic_progress_columns, time_allocation


def _daily(journal: pd.DataFrame, column: str, how: str = "mean") -> pd.Series:
    return journal.groupby("day_index")[column].agg(how)


def plot_trajectories(journal: pd.DataFrame, output_dir: str) -> str:
    fig, axes = plt.subplots(3, 2, figsize=(12, 10), sharex=True)
    series_specs = [
        ("money", "Argent (FCFA)", "tab:green"),
        ("health", "Santé", "tab:red"),
        ("stress", "Stress", "tab:orange"),
        ("fatigue", "Fatigue", "tab:purple"),
        ("moral", "Moral", "tab:blue"),
        ("hunger", "Faim", "tab:brown"),
    ]
    for ax, (col, label, color) in zip(axes.flat, series_specs):
        daily = _daily(journal, col)
        ax.plot(daily.index, daily.values, color=color)
        ax.set_title(label)
        ax.set_xlabel("Jour")
        ax.grid(alpha=0.3)
    fig.suptitle("Trajectoires quotidiennes (moyenne journalière)")
    fig.tight_layout()
    path = os.path.join(output_dir, "trajectories.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_academic_progress(journal: pd.DataFrame, output_dir: str) -> str:
    cols = academic_progress_columns(journal)
    fig, ax = plt.subplots(figsize=(10, 5))
    for col in cols:
        daily = _daily(journal, col, how="last")
        ax.plot(daily.index, daily.values, label=col.replace("academic_", ""))
    ax.set_title("Progression académique par matière")
    ax.set_xlabel("Jour")
    ax.set_ylabel("Progression (0-100)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(output_dir, "academic_progress.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_time_allocation(journal: pd.DataFrame, output_dir: str) -> str:
    allocation = time_allocation(journal)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(allocation.values, labels=allocation.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("Répartition du temps par catégorie d'action")
    fig.tight_layout()
    path = os.path.join(output_dir, "time_allocation.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_exam_results(exam_results: pd.DataFrame, output_dir: str) -> str | None:
    if exam_results.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["tab:green" if p else "tab:red" for p in exam_results["passed"]]
    labels = exam_results["subject"] + "\n" + exam_results["date"]
    ax.bar(labels, exam_results["score"], color=colors)
    ax.axhline(50, color="black", linestyle="--", linewidth=1, label="Seuil de réussite")
    ax.set_title("Résultats aux examens")
    ax.set_ylabel("Score")
    ax.legend()
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    path = os.path.join(output_dir, "exam_results.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def generate_all_plots(journal: pd.DataFrame, exam_results: pd.DataFrame, output_dir: str) -> list[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    paths = [
        plot_trajectories(journal, output_dir),
        plot_academic_progress(journal, output_dir),
        plot_time_allocation(journal, output_dir),
    ]
    exam_plot = plot_exam_results(exam_results, output_dir)
    if exam_plot:
        paths.append(exam_plot)
    return paths
