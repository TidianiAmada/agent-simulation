"""Orchestre l'ordre d'exécution des cycles (section 2 / core/scheduler.py)."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from agents.student import Student
from config.schema import AgentProfile, SimulationConfig
from core.clock import SimClock
from core.environment import Environment
from events import Event, default_events


class Scheduler:
    def __init__(self, sim_config: SimulationConfig, agent_profile: AgentProfile, events: list[Event] | None = None):
        self.sim_config = sim_config
        self.agent_profile = agent_profile
        self.rng = np.random.default_rng(sim_config.seed)
        self.clock = SimClock(sim_config.start_date, sim_config.duration_days, sim_config.time_step_hours)
        self.environment = Environment(sim_config, agent_profile, self.clock, self.rng)
        self.student = Student(agent_profile, self.rng, self.clock.current_datetime)
        self.events = events if events is not None else default_events()

        self.journal: list[dict[str, Any]] = []
        self.event_log: list[dict[str, Any]] = []

    def run(self) -> pd.DataFrame:
        dt_hours = self.sim_config.time_step_hours  # amorçage du tout premier cycle
        while not self.clock.is_finished():
            self.clock.advance(dt_hours)

            triggered = []
            for event in self.events:
                occurrence = event.check_and_apply(self.environment, self.student, dt_hours)
                if occurrence is not None:
                    triggered.append(occurrence.name)
                    self.event_log.append(
                        {
                            "day_index": occurrence.day_index,
                            "datetime": self.clock.current_datetime,
                            "event": occurrence.name,
                            "description": occurrence.description,
                        }
                    )

            day_index = self.clock.day_index
            record, next_dt_hours = self.student.step(self.environment, day_index, dt_hours)
            record["events"] = ",".join(triggered)
            self.journal.append(record)
            dt_hours = next_dt_hours

        return pd.DataFrame(self.journal)

    def events_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.event_log)

    def exam_results_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.student.exam_results)
