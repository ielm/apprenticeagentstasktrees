from backend.models.grammar import Grammar
from backend.models.graph import Frame, Graph, Identifier, Literal
from backend.models.statement import Statement, VariableMap
from enum import Enum
from functools import reduce
from typing import Any, Dict, List, Tuple, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.agent import Agent
    from backend.models.effectors import Capability


class Agenda(object):

    def __init__(self, frame: Frame):
        self.frame = frame

    def goals(self, pending=False, active=True, abandoned=False, satisfied=False):
        results = list(map(lambda g: Goal(g.resolve()), self.frame["HAS-GOAL"]))

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

        self.frame["HAS-GOAL"] += goal

    def prepare_action(self, action: Union['Action', Frame]):
        if isinstance(action, Action):
            action = action.frame

        self.frame["ACTION-TO-TAKE"] += action

    def action(self):
        if "ACTION-TO-TAKE" not in self.frame:
            return []

        return list(map(lambda a: Action(a.resolve()), self.frame["ACTION-TO-TAKE"]))

        # return Action(self.frame["ACTION-TO-TAKE"].singleton())


class Goal(VariableMap):

    class Status(Enum):
        PENDING = 1
        ACTIVE = 2
        ABANDONED = 3
        SATISFIED = 4

    @classmethod
    def define(cls, graph: Graph, name: str, priority: Union[Statement, float], resources: Union[Statement, float], plan: List['Action'], conditions: List['Condition'], variables: List[str]):
        frame = graph.register(name, generate_index=False)
        frame["NAME"] = Literal(name)
        frame["PRIORITY"] = priority
        frame["RESOURCES"] = resources
        frame["PLAN"] = list(map(lambda p: p.frame, plan))
        frame["WHEN"] = list(map(lambda c: c.frame, conditions))
        frame["WITH"] = list(map(lambda var: Literal(var), variables))

        return Goal(frame)

    @classmethod
    def instance_of(cls, graph: Graph, definition: Union[Frame, 'Goal'], params: List[Any], existing: Union[str, Identifier, Frame]=None):
        if isinstance(definition, Goal):
            definition = definition.frame

        if existing is not None:
            if isinstance(existing, str):
                existing = Identifier.parse(existing)
            if isinstance(existing, Identifier):
                existing = existing.resolve(graph)

        frame = existing if existing is not None else graph.register("GOAL", isa=definition._identifier, generate_index=True)
        frame["NAME"] = definition["NAME"]
        frame["PRIORITY"] = definition["PRIORITY"]
        frame["RESOURCES"] = definition["RESOURCES"]
        frame["STATUS"] = Goal.Status.PENDING
        frame["PLAN"] = definition["PLAN"]
        frame["WHEN"] = definition["WHEN"]

        super().instance_of(graph, definition, params, existing=frame)

        return Goal(frame)

    @classmethod
    def parse(cls, agent: 'Agent', input: str) -> 'Goal':
        result = Grammar.parse(agent, input, start="define", agent=agent)

        if not isinstance(result, Goal):
            raise Exception("Parsed value for \"" + input + "\" is not a Goal.")

        return result

    def __init__(self, frame: Frame):
        super().__init__(frame)

    def name(self) -> str:
        if "NAME" in self.frame:
            return self.frame["NAME"].singleton()
        return "Unknown Goal"

    def is_pending(self) -> bool:
        return Goal.Status.PENDING.name.lower() in self.frame["STATUS"] or Goal.Status.PENDING.name in self.frame["STATUS"] or Goal.Status.PENDING in self.frame["STATUS"]

    def is_active(self) -> bool:
        return Goal.Status.ACTIVE.name.lower() in self.frame["STATUS"] or Goal.Status.ACTIVE.name in self.frame["STATUS"] or Goal.Status.ACTIVE in self.frame["STATUS"]

    def is_abandoned(self) -> bool:
        return Goal.Status.ABANDONED.name.lower() in self.frame["STATUS"] or Goal.Status.ABANDONED.name in self.frame["STATUS"] or Goal.Status.ABANDONED in self.frame["STATUS"]

    def is_satisfied(self) -> bool:
        return Goal.Status.SATISFIED.name.lower() in self.frame["STATUS"] or Goal.Status.SATISFIED.name in self.frame["STATUS"] or Goal.Status.SATISFIED in self.frame["STATUS"]

    def status(self, status: 'Goal.Status'):
        self.frame["STATUS"] = status

    def assess(self):
        if self.reserved_effector() is not None:
            return

        conditions = sorted(self.conditions(), key=lambda condition: condition.order())
        for condition in conditions:
            if condition.assess(self):
                self.status(condition.status())
                return

    def conditions(self) -> List['Condition']:
        return list(map(lambda condition: Condition(condition.resolve()), self.frame["WHEN"]))

    def subgoals(self) -> List['Goal']:
        return list(map(lambda goal: Goal(goal.resolve()), self.frame["HAS-GOAL"]))

    def priority(self, agent: 'Agent'):
        try:
            stmt: Statement = Statement.from_instance(self.frame["PRIORITY"].singleton())
            priority = stmt.run(self)

            self.frame["_PRIORITY"] = priority
            return priority
        except: pass # Not a Statement

        try:
            priority = self.frame["PRIORITY"].singleton()

            self.frame["_PRIORITY"] = priority
            return priority
        except:
            priority = 0.0

            self.frame["_PRIORITY"] = priority
            return priority

    def _cached_priority(self):
        if "_PRIORITY" in self.frame:
            return self.frame["_PRIORITY"].singleton()
        return 0.0

    def resources(self, agent: 'Agent'):
        try:
            stmt: Statement = Statement.from_instance(self.frame["RESOURCES"].singleton())
            resources = stmt.run(self)

            self.frame["_RESOURCES"] = resources
            return resources
        except: pass # Not a Statement

        try:
            resources = self.frame["RESOURCES"].singleton()

            self.frame["_RESOURCES"] = resources
            return resources
        except:
            resources = 1.0

            self.frame["_RESOURCES"] = resources
            return resources

    def _cached_resources(self):
        if "_RESOURCES" in self.frame:
            return self.frame["_RESOURCES"].singleton()
        return 1.0

    def decision(self, decide: float=None):
        if decide is not None:
            self.frame["_DECISION"] = decide

        if "_DECISION" in self.frame:
            return self.frame["_DECISION"].singleton()
        return 0.0

    def plan(self) -> 'Action':
        for plan in self.frame["PLAN"]:
            action = Action(plan.resolve())
            if action.select(self):
                return action
        raise Exception("No action was selected in the plan.")

    def reserved_effector(self) -> 'Effector':
        from backend.models.effectors import Effector

        for u in self.frame["USES"]:
            u = u.resolve()
            if u ^ "EXE.EFFECTOR":
                return Effector(u)
        return None

    def __eq__(self, other):
        if isinstance(other, Goal):
            return self.frame == other.frame or (
                self.frame["NAME"] == other.frame["NAME"] and
                self.frame["PRIORITY"] == other.frame["PRIORITY"] and
                self.frame["STATUS"] == other.frame["STATUS"] and
                self.__eqPLAN(other) and
                self.__eqWHEN(other)
            )
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)

    def __eqPLAN(self, other: 'Goal'):
        if self.frame["PLAN"] == other.frame["PLAN"]:
            return True

        s1 = list(map(lambda frame: Action(frame.resolve()), self.frame["PLAN"]))
        s2 = list(map(lambda frame: Action(frame.resolve()), other.frame["PLAN"]))

        return s1 == s2

    def __eqWHEN(self, other: 'Goal'):
        if self.frame["WHEN"] == other.frame["WHEN"]:
            return True

        s1 = list(map(lambda frame: Condition(frame.resolve()), self.frame["WHEN"]))
        s2 = list(map(lambda frame: Condition(frame.resolve()), other.frame["WHEN"]))

        return s1 == s2


class Action(object):

    DEFAULT = "DEFAULT"
    IDLE = "IDLE"

    @classmethod
    def build(cls, graph: Graph, name: str, select: Union[Statement, str], perform: Union[Statement, str, List[Union[Statement, str]]]):

        if isinstance(select, Statement):
            select = select.frame

        if not isinstance(perform, List):
            perform = [perform]
        perform = list(map(lambda p: Literal(Action.IDLE) if p == Action.IDLE else p.frame, perform))

        frame = graph.register("ACTION", generate_index=True)
        frame["NAME"] = Literal(name)
        frame["SELECT"] = Literal(Action.DEFAULT) if select == Action.DEFAULT else select
        frame["PERFORM"] = perform

        return Action(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def name(self) -> str:
        if "NAME" in self.frame:
            return self.frame["NAME"].singleton()

    def select(self, varmap: VariableMap) -> bool:
        if self.is_default():
            return True

        if "SELECT" in self.frame:
            select = self.frame["SELECT"].singleton()
            if isinstance(select, Frame) and select ^ "EXE.BOOLEAN-STATEMENT":
                return Statement.from_instance(select).run(varmap)
        return False

    def is_default(self):
        if "SELECT" in self.frame:
            select = self.frame["SELECT"].singleton()
            if select == Action.DEFAULT:
                return True
        return False

    def perform(self, varmap: VariableMap):
        for statement in self.frame["PERFORM"]:
            statement = statement.resolve()
            if statement == Action.IDLE:
                pass
            if isinstance(statement, Frame) and statement ^ "EXE.STATEMENT":
                Statement.from_instance(statement).run(varmap)

    def capabilities(self) -> List['Capability']:
        do: List[Statement] = list(map(lambda do: Statement.from_instance(do), filter(lambda do: do != Action.IDLE, map(lambda do: do.resolve(), self.frame["PERFORM"]))))
        capabilities = []
        for stmt in do:
            capabilities.extend(stmt.capabilities())
        return capabilities

    def __eq__(self, other):
        if isinstance(other, Action):
            return (self.frame == other.frame) or (
                self.frame["NAME"] == other.frame["NAME"] and
                self.__eqSELECT(other) and
                self.__eqPERFORM(other)
            )
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)

    def __eqSELECT(self, other: 'Action'):
        if self.frame["SELECT"] == other.frame["SELECT"]:
            return True
        if self.frame["SELECT"] == Action.DEFAULT or other.frame["SELECT"] == Action.DEFAULT:
            return False

        s1 = list(map(lambda frame: Statement.from_instance(frame.resolve()), self.frame["SELECT"]))
        s2 = list(map(lambda frame: Statement.from_instance(frame.resolve()), other.frame["SELECT"]))

        return s1 == s2

    def __eqPERFORM(self, other: 'Action'):
        if self.frame["PERFORM"] == other.frame["PERFORM"]:
            return True
        if self.frame["PERFORM"] == Action.IDLE or other.frame["PERFORM"] == Action.IDLE:
            return False

        s1 = list(map(lambda frame: Statement.from_instance(frame.resolve()), self.frame["PERFORM"]))
        s2 = list(map(lambda frame: Statement.from_instance(frame.resolve()), other.frame["PERFORM"]))

        return s1 == s2


class Condition(object):

    @classmethod
    def build(cls, graph: Graph, statements: List[Statement], status: Goal.Status, logic: 'Condition.Logic'=1, order: int=1):
        frame = graph.register("CONDITION", generate_index=True)
        frame["IF"] = list(map(lambda statement: statement.frame, statements))
        frame["LOGIC"] = logic
        frame["STATUS"] = status
        frame["ORDER"] = order

        return Condition(frame)

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
            return self.frame["ORDER"].singleton()

    def status(self) -> Goal.Status:
        if "STATUS" in self.frame:
            status = self.frame["STATUS"].singleton()
            if isinstance(status, Goal.Status):
                return status
            if isinstance(status, str):
                return Goal.Status[status]

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
            value = self.frame["LOGIC"].singleton()
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
            return self.frame == other.frame or (
                self.__eqIF(other) and
                self.frame["LOGIC"] == other.frame["LOGIC"] and
                self.frame["STATUS"] == other.frame["STATUS"] and
                self.frame["ORDER"] == other.frame["ORDER"]
            )
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)

    def __eqIF(self, other: 'Condition'):
        if self.frame["IF"] == other.frame["IF"]:
            return True

        s1 = list(map(lambda frame: Statement.from_instance(frame.resolve()), self.frame["IF"]))
        s2 = list(map(lambda frame: Statement.from_instance(frame.resolve()), other.frame["IF"]))

        return s1 == s2