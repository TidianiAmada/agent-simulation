from actions.base import Action, ActionCategory
from actions.eat import BudgetMeal, NormalMeal
from actions.finance import RequestFamilyHelp
from actions.leisure import Rest, Socialize
from actions.sleep import Sleep
from actions.study import AttendCourse, Review
from actions.work import WorkShift

ALL_ACTIONS: list[Action] = [
    WorkShift(),
    BudgetMeal(),
    NormalMeal(),
    AttendCourse(),
    Review(),
    Sleep(),
    Rest(),
    Socialize(),
    RequestFamilyHelp(),
]

__all__ = [
    "Action",
    "ActionCategory",
    "WorkShift",
    "BudgetMeal",
    "NormalMeal",
    "AttendCourse",
    "Review",
    "Sleep",
    "Rest",
    "Socialize",
    "RequestFamilyHelp",
    "ALL_ACTIONS",
]
