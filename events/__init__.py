from events.base import Event, EventOccurrence
from events.exam import ExamEvent
from events.family_help import FamilyHelpEvent
from events.illness import IllnessEvent
from events.inflation import InflationEvent
from events.job_loss import JobLossEvent
from events.rent import RentEvent


def default_events() -> list[Event]:
    """Ordre : calendaires d'abord (examens/loyer), puis probabilistes (section 11)."""
    return [
        ExamEvent(),
        RentEvent(),
        InflationEvent(),
        IllnessEvent(),
        JobLossEvent(),
        FamilyHelpEvent(),
    ]


__all__ = [
    "Event",
    "EventOccurrence",
    "ExamEvent",
    "RentEvent",
    "InflationEvent",
    "IllnessEvent",
    "JobLossEvent",
    "FamilyHelpEvent",
    "default_events",
]
