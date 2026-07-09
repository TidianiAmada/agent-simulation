"""Pile d'intentions courantes, engagement et abandon de plan (section 3.3)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from actions.base import Action
    from agents.beliefs import Beliefs
    from agents.desires import Desire
    from core.environment import Environment


@dataclass
class Intention:
    goal_name: str
    plan: list["Action"] = field(default_factory=list)
    created_at_day: int = 0

    def is_exhausted(self) -> bool:
        return len(self.plan) == 0

    def peek(self) -> "Action | None":
        return self.plan[0] if self.plan else None

    def consume(self, action: "Action") -> None:
        if self.plan and self.plan[0] is action:
            self.plan.pop(0)
        elif action in self.plan:
            self.plan.remove(action)


class IntentionStack:
    def __init__(self) -> None:
        self._stack: list[Intention] = []

    @property
    def current(self) -> Intention | None:
        return self._stack[-1] if self._stack else None

    def push(self, intention: Intention) -> None:
        self._stack.append(intention)

    def replace_current(self, intention: Intention) -> None:
        if self._stack:
            self._stack[-1] = intention
        else:
            self._stack.append(intention)

    def abandon_current(self) -> None:
        if self._stack:
            self._stack.pop()

    def is_empty(self) -> bool:
        return len(self._stack) == 0


def needs_replanning(
    intention: Intention | None,
    dominant_desire: "Desire",
    beliefs: "Beliefs",
    environment: "Environment",
    priority_threshold: float,
    force_replan: bool,
) -> bool:
    """Conditions d'abandon/replanification (section 3.3)."""
    if force_replan:
        return True
    if intention is None or intention.is_exhausted():
        return True
    if intention.goal_name != dominant_desire.name and dominant_desire.intensity >= priority_threshold:
        return True
    next_action = intention.peek()
    if next_action is not None and not next_action.preconditions(beliefs, environment):
        return True
    return False
