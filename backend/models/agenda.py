from backend.models.graph import Frame
from backend.models.mps import MPRegistry
from enum import Enum
from typing import List

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.agent import Agent


class Agenda(object):

    def __init__(self, frame: Frame):
        pass

    '''
    HAS-GOAL GOAL
    SELECTED-ACTION ACTION  // blanked, and then reselected each time interval
    '''


class Goal(object):

    class Status(Enum):
        PENDING = 1
        ACTIVE = 2
        ABANDONED = 3
        SATISFIED = 4

    def __init__(self, frame: Frame):
        self.frame = frame

    def is_pending(self) -> bool:
        return Goal.Status.PENDING.name.lower() in self.frame["STATUS"]

    def is_active(self) -> bool:
        return Goal.Status.ACTIVE.name.lower() in self.frame["STATUS"]

    def is_abandoned(self) -> bool:
        return Goal.Status.ABANDONED.name.lower() in self.frame["STATUS"]

    def is_satisfied(self) -> bool:
        return Goal.Status.SATISFIED.name.lower() in self.frame["STATUS"]

    def status(self, status: 'Goal.Status'):
        self.frame["STATUS"] = status.name.lower()

    def assess(self):
        for desired in self.frame["GOAL-STATE"]:
            desired = desired.resolve()
            domain = desired["DOMAIN"][0].resolve()
            property = desired._identifier.name
            if domain[property] != desired["RANGE"]:
                return

        self.status(Goal.Status.SATISFIED)

    def subgoals(self) -> List['Goal']:
        return list(map(lambda goal: Goal(goal), self.frame["HAS-GOAL"]))

    def prioritize(self, agent: 'Agent'):
        priority = max(map(lambda mp: MPRegistry[mp.resolve()["CALLS"][0].resolve().value](agent), self.frame["PRIORITY-CALCULATION"]))
        self.frame["PRIORITY"] = priority

    def priority(self):
        if "PRIORITY" in self.frame:
            return self.frame["PRIORITY"][0].resolve().value
        return 0.0

    def pursue(self, agent: 'Agent') -> 'Action':
        if len(self.frame["ACTION-SELECTION"]) != 1:
            raise Exception("No action selection MPs available.")

        return Action(MPRegistry[self.frame["ACTION-SELECTION"][0].resolve()["CALLS"][0].resolve().value](agent))


class Action(object):

    def __init__(self, frame: Frame):
        self.frame = frame