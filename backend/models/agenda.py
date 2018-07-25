from backend.models.graph import Frame
from backend.models.mps import MPRegistry
from enum import Enum
from typing import List, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.agent import Agent


class Agenda(object):

    def __init__(self, frame: Frame):
        self.frame = frame

    def goals(self, pending=False, active=True, abandoned=False, satisfied=False):
        results = map(lambda g: Goal(g.resolve()), self.frame["GOAL"])

        if not pending:
            results = filter(lambda g: not g.is_pending(), results)

        if not active:
            results = filter(lambda g: not g.is_active(), results)

        if not abandoned:
            results = filter(lambda g: not g.is_abandoned(), results)

        if not satisfied:
            results = filter(lambda g: not g.is_satisfied(), results)

        return list(results)

    def add_goal(self, goal: Union['Goal', Frame]):
        if isinstance(goal, Goal):
            goal = goal.frame

        if "STATUS" not in goal:
            goal["STATUS"] = Goal.Status.PENDING

        self.frame["GOAL"] += goal

    def prepare_action(self, action: Union['Action', Frame]):
        if isinstance(action, Action):
            action = action.frame

        self.frame["ACTION-TO-TAKE"] = action

    def action(self):
        return Action(self.frame["ACTION-TO-TAKE"][0].resolve())


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

    def inherit(self):
        # Grabs choice fields from the definition of this goal (from the immediate parent); in some cases it just
        # links them locally, while in others it creates an instance (such as subgoals).  In all cases, this is
        # non-destructive to fields that already exist.

        parents = list(map(lambda isa: isa.resolve(), self.frame[self.frame._ISA_type()]))
        for parent in parents:
            self.frame["PRIORITY-CALCULATION"] += parent["PRIORITY-CALCULATION"]
            self.frame["ACTION-SELECTION"] += parent["ACTION-SELECTION"]

    def __eq__(self, other):
        if isinstance(other, Goal):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class Action(object):

    def __init__(self, frame: Frame):
        self.frame = frame

    def execute(self, agent: 'Agent'):
        MPRegistry[self.frame["RUN"][0].resolve()["CALLS"][0].resolve().value](agent)

    def __eq__(self, other):
        if isinstance(other, Action):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)