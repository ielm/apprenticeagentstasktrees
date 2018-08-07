from backend.models.graph import Frame, Graph, Identifier, Literal, Slot
from backend.models.mps import Executable, MeaningProcedure, MPRegistry
from backend.models.statement import Statement, VariableMap
from enum import Enum
from functools import reduce
from typing import Any, Callable, Dict, List, Tuple, Union

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

    @classmethod
    def register(cls,
                 graph: Graph, name: str,
                 pcalc: List[Callable]=None,
                 aselect: List[Callable]=None,
                 condition: List[Tuple[Union[str, Identifier], Union[str, Slot], Any]]=None,
                 set_status: 'Goal.Status'=None
                 ) -> 'Goal':
        if pcalc is None:
            pcalc = []

        if aselect is None:
            aselect = []

        if condition is None:
            condition = []

        if set_status is None:
            set_status = Goal.Status.SATISFIED

        goal = graph.register("AGENDA-GOAL", generate_index=True)

        for f in pcalc:
            mp = graph.register("MEANING-PROCEDURE", generate_index=True)
            mp["CALLS"] = Literal(f.__name__)
            MPRegistry.register(f)
            goal["PRIORITY-CALCULATION"] += mp

        for f in aselect:
            mp = graph.register("MEANING-PROCEDURE", generate_index=True)
            mp["CALLS"] = Literal(f.__name__)
            MPRegistry.register(f)
            goal["ACTION-SELECTION"] += mp

        if len(condition) > 0:
            c = graph.register("GOAL-CONDITION", generate_index=True)
            c["LOGIC"] = Literal(Condition.Logic.AND.name)
            c["APPLY-STATUS"] = Literal(set_status.name)
            goal["ON-CONDITION"] += c
            for t in condition:
                property = t[1]
                if isinstance(t[1], Slot):
                    property = t[1]._name

                p = graph.register(property.upper(), generate_index=True)
                p["DOMAIN"] = t[0]
                p["RANGE"] = t[2]
                c["WITH-CONDITION"] += p

        return Goal(goal)

    def __init__(self, frame: Frame):
        self.frame = frame

    def name(self) -> str:
        if "NAME" in self.frame:
            return self.frame["NAME"][0].resolve().value
        return "Unknown Goal"

    def is_pending(self) -> bool:
        return Goal.Status.PENDING.name.lower() in self.frame["STATUS"] or Goal.Status.PENDING.name in self.frame["STATUS"]

    def is_active(self) -> bool:
        return Goal.Status.ACTIVE.name.lower() in self.frame["STATUS"] or Goal.Status.ACTIVE.name in self.frame["STATUS"]

    def is_abandoned(self) -> bool:
        return Goal.Status.ABANDONED.name.lower() in self.frame["STATUS"] or Goal.Status.ABANDONED.name in self.frame["STATUS"]

    def is_satisfied(self) -> bool:
        return Goal.Status.SATISFIED.name.lower() in self.frame["STATUS"] or Goal.Status.SATISFIED.name in self.frame["STATUS"]

    def status(self, status: 'Goal.Status'):
        self.frame["STATUS"] = status.name.lower()

    def assess(self):
        conditions = sorted(self.conditions(), key=lambda condition: condition.order())
        for condition in conditions:
            if condition.assess():
                self.status(condition.status())
                return

    def conditions(self) -> List['Condition']:
        return list(map(lambda condition: Condition(condition.resolve()), self.frame["ON-CONDITION"]))

    def subgoals(self) -> List['Goal']:
        return list(map(lambda goal: Goal(goal.resolve()), self.frame["HAS-GOAL"]))

    def prioritize(self, agent: 'Agent'):
        if "PRIORITY" in self.frame:
            priority = self.frame["PRIORITY"][0].resolve()
            if isinstance(priority, Literal):
                self.frame["_PRIORITY"] = priority.value
            else:
                self.frame["_PRIORITY"] = -1.0 # TODO: evaluate a CALCULATE-STATEMENT

        return 0.0

    def priority(self):
        if "_PRIORITY" in self.frame:
            return self.frame["_PRIORITY"][0].resolve().value
        return 0.0

    def pursue(self, agent: 'Agent') -> 'Action':
        if len(self.frame["ACTION-SELECTION"]) != 1:
            raise Exception("No action selection MPs available.")

        return Action(MeaningProcedure(self.frame["ACTION-SELECTION"][0].resolve()).run(agent))

    def inherit(self):
        # Grabs choice fields from the definition of this goal (from the immediate parent); in some cases it just
        # links them locally, while in others it creates an instance (such as subgoals).  In all cases, this is
        # non-destructive to fields that already exist.

        parents = list(map(lambda isa: isa.resolve(), self.frame[self.frame._ISA_type()]))
        for parent in parents:
            self.frame["PRIORITY-CALCULATION"] = self.frame["PRIORITY-CALCULATION"] + parent["PRIORITY-CALCULATION"] # TODO: why doesn't += work the way it should?
            self.frame["ACTION-SELECTION"] = self.frame["ACTION-SELECTION"] + parent["ACTION-SELECTION"]
            self.frame["ON-CONDITION"] = self.frame["ON-CONDITION"] + parent["ON-CONDITION"]

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
        Executable(self.frame).run(agent)

    def __eq__(self, other):
        if isinstance(other, Action):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class Condition(object):

    class Logic(Enum):
        AND = 1
        OR = 2
        NOR = 3
        NAND = 4
        NOT = 5

    def __init__(self, frame: Frame):
        self.frame = frame

        for statement in self.frame["IF"]:
            if not statement ^ "EXE.BOOLEAN-STATEMENT":
                raise Exception("IF statement is not a BOOLEAN-STATEMENT.")

    def order(self) -> int:
        if "ORDER" in self.frame:
            return self.frame["ORDER"][0].resolve().value

    def status(self) -> Goal.Status:
        if "STATUS" in self.frame:
            return Goal.Status[self.frame["STATUS"][0].resolve().value]

    def assess(self, varmap: VariableMap) -> bool:
        if "IF" not in self.frame:
            return True

        results = map(lambda wc: self._assess_if(wc.resolve(), varmap), self.frame["IF"])

        if self.logic() == Condition.Logic.AND:
            return reduce(lambda x, y: x and y, results)
        if self.logic() == Condition.Logic.OR:
            return reduce(lambda x, y: x or y, results)
        if self.logic() == Condition.Logic.NOR:
            return not reduce(lambda x, y: x or y, results)
        if self.logic() == Condition.Logic.NAND:
            return not reduce(lambda x, y: x and y, results)
        if self.logic() == Condition.Logic.NOT:
            return not reduce(lambda x, y: x or y, results)

    def logic(self):
        if "LOGIC" in self.frame:
            value = self.frame["LOGIC"][0].resolve().value
            if isinstance(value, Condition.Logic):
                return value
            if isinstance(value, str):
                return Condition.Logic[value.upper()]
        return Condition.Logic.AND

    def _assess_if(self, frame: Frame, varmap: VariableMap) -> bool:
        if not frame ^ "EXE.BOOLEAN-STATEMENT":
            raise Exception("IF statement is not a BOOLEAN-STATEMENT.")
        return Statement.from_instance(frame).run(varmap)

    def __eq__(self, other):
        if isinstance(other, Condition):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class Variable(object):

    def __init__(self, name: str):
        self.name = name

    def resolve(self, mappings: Dict[str, Union[str, Identifier, Frame]]):
        if mappings is None:
            raise Exception("Cannot resolve variable with unknown mappings.")
        if self.name not in mappings:
            raise Exception("Variable '" + self.name + "' is not in target mappings.")

        resolved = mappings[self.name]

        if isinstance(resolved, str):
            resolved = Identifier.parse(resolved)
        if isinstance(resolved, Identifier):
            resolved = resolved.resolve(None)
        if not isinstance(resolved, Frame):
            raise Exception("Cannot resolve variable '" + self.name + "' into a frame.")

        return resolved