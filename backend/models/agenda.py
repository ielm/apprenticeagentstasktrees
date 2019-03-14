# from backend.models.grammar import Grammar
# from backend.models.graph import Frame, Graph, Identifier, Literal
# from backend.models.query import Query
from backend.models.statement import AssertStatement, MakeInstanceStatement, Statement, StatementScope, VariableMap
from enum import Enum
from functools import reduce
from typing import Any, Dict, List, Tuple, Union

from ontograph import graph
from ontograph.Frame import Frame, Role
from ontograph.Graph import Graph
from ontograph.Index import Identifier
from ontograph.Query import Query
from ontograph.Space import Space

import time

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.agent import Agent
    from backend.models.effectors import Callback, Capability, Effector
    from backend.models.output import XMR


class Agenda(object):

    def __init__(self, frame: Frame):
        self.frame = frame

    def goals(self, pending=False, active=True, abandoned=False, satisfied=False):
        results = map(lambda g: Goal(g), self.frame["HAS-GOAL"])

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

    def prepare_plan(self, plan: Union['Plan', Frame]):
        if isinstance(plan, Plan):
            plan = plan.frame

        self.frame["PLAN-TO-TAKE"] += plan

    def plan(self):
        if "PLAN-TO-TAKE" not in self.frame:
            return []

        return list(map(lambda a: Plan(a), self.frame["PLAN-TO-TAKE"]))

    def add_trigger(self, trigger: [str, Identifier, Frame, 'Trigger']):
        if isinstance(trigger, str):
            trigger = Frame(trigger)
        if isinstance(trigger, Trigger):
            trigger = trigger.frame
        if isinstance(trigger, Identifier):
            trigger = Frame(trigger.id)

        self.frame["TRIGGER"] += trigger

    def triggers(self) -> List['Trigger']:
        return list(map(lambda t: Trigger(t), self.frame["TRIGGER"]))

    def fire_triggers(self):
        for trigger in self.triggers():
            trigger.fire(self)


class Goal(VariableMap):

    class Status(Enum):
        PENDING = 1
        ACTIVE = 2
        ABANDONED = 3
        SATISFIED = 4

    @classmethod
    def define(cls, space: Space, name: str, priority: Union[Statement, float], resources: Union[Statement, float], plan: List['Plan'], conditions: List['Condition'], variables: List[str], effects: List['Effect']):
        frame = Frame("@" + space.name + "." + name)
        frame["NAME"] = name
        frame["PRIORITY"] = priority
        frame["RESOURCES"] = resources
        frame["PLAN"] = list(map(lambda p: p.frame, plan))
        frame["WHEN"] = list(map(lambda c: c.frame, conditions))
        frame["WITH"] = variables
        frame["HAS-EFFECT"] = list(map(lambda e: e.frame, effects))

        return Goal(frame)

    @classmethod
    def instance_of(cls, space: Space, definition: Union[Frame, 'Goal'], params: List[Any], existing: Union[str, Identifier, Frame]=None):
        if isinstance(definition, Goal):
            definition = definition.frame

        if existing is not None:
            if isinstance(existing, str):
                existing = Frame(existing)
            if isinstance(existing, Identifier):
                existing = Frame(existing.id)

        frame = existing
        if frame is None:
            frame = Frame("@" + space.name + ".GOAL.?").add_parent(definition)
        frame["NAME"] = list(definition["NAME"])
        frame["PRIORITY"] = list(definition["PRIORITY"])
        frame["RESOURCES"] = list(definition["RESOURCES"])
        frame["STATUS"] = Goal.Status.PENDING
        frame["PLAN"] = list(map(lambda plan: Plan.instance_of(space, plan).frame, definition["PLAN"]))
        frame["WHEN"] = list(definition["WHEN"])
        frame["HAS-EFFECT"] = list(definition["HAS-EFFECT"])

        super().instance_of(space, definition, params, existing=frame)

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
        slot = self.frame["NAME", Role.LOC]
        if len(slot) == 1:
            return slot.singleton()
        slot = self.frame["NAME"]
        if len(slot) == 1:
            return slot.singleton()
        # if "NAME" in self.frame:
        #     return self.frame["NAME"].singleton()
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

    def executed(self) -> bool:
        for plan in self.plans():
            if plan.executed():
                return True
        return False

    def assess(self):
        conditions = sorted(self.conditions(), key=lambda condition: condition.order())
        for condition in conditions:
            if condition.assess(self):
                self.status(condition.status())
                break

        if self.is_abandoned() or self.is_satisfied():
            for subgoal in self.subgoals():
                if not subgoal.is_satisfied():
                    subgoal.frame["STATUS"] = Goal.Status.ABANDONED

        if self.is_satisfied():
            for effect in self.effects():
                effect.apply(self)

    def conditions(self) -> List['Condition']:
        return list(map(lambda condition: Condition(condition), self.frame["WHEN"]))

    def subgoals(self) -> List['Goal']:
        return list(map(lambda goal: Goal(goal), self.frame["HAS-GOAL"]))

    def effects(self) -> List['Effect']:
        return list(map(lambda effect: Effect(effect), self.frame["HAS-EFFECT"]))

    def priority(self):
        try:
            stmt: Statement = Statement.from_instance(self.frame["PRIORITY", Role.LOC].singleton())
            priority = stmt.run(StatementScope(), self)

            self.frame["_PRIORITY"] = priority
            return priority
        except: pass # Not a Statement

        try:
            priority = self.frame["PRIORITY", Role.LOC].singleton()

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

    def resources(self):
        try:
            stmt: Statement = Statement.from_instance(self.frame["RESOURCES"].singleton())
            resources = stmt.run(StatementScope(), self)

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

    def plan(self) -> 'Plan':
        for plan in self.frame["PLAN", Role.LOC]:
            plan = Plan(plan)
            if plan.select(self):
                return plan
        raise Exception("No plan was selected.")

    def plans(self) -> List['Plan']:
        return list(map(lambda plan: Plan(plan), self.frame["PLAN", Role.LOC]))

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
        if self.frame["PLAN", Role.LOC] == other.frame["PLAN", Role.LOC]:
            return True

        s1 = list(map(lambda frame: Plan(frame.resolve()), self.frame["PLAN", Role.LOC]))
        s2 = list(map(lambda frame: Plan(frame.resolve()), other.frame["PLAN", Role.LOC]))

        return s1 == s2

    def __eqWHEN(self, other: 'Goal'):
        if self.frame["WHEN"] == other.frame["WHEN"]:
            return True

        s1 = list(map(lambda frame: Condition(frame.resolve()), self.frame["WHEN"]))
        s2 = list(map(lambda frame: Condition(frame.resolve()), other.frame["WHEN"]))

        return s1 == s2


class Plan(object):

    DEFAULT = "DEFAULT"

    @classmethod
    def build(cls, space: Space, name: str, select: Union[Statement, Frame, str], steps: Union['Step', Frame, List[Union['Step', Frame]]], negate: bool=False):

        if isinstance(select, Statement):
            select = select.frame

        if not isinstance(steps, List):
            steps = [steps]
        steps = list(map(lambda s: s.frame if isinstance(s, Step) else s, steps))

        frame = Frame("@" + space.name + ".PLAN.?")
        frame["NAME"] = name
        frame["NEGATE"] = negate
        frame["SELECT"] = select
        frame["HAS-STEP"] = steps

        return Plan(frame)

    @classmethod
    def instance_of(cls, space: Space, plan: Union[Frame, 'Plan']) -> 'Plan':

        if isinstance(plan, Frame):
            plan = Plan(plan)

        return Plan.build(space, plan.name(), plan.frame["SELECT"].singleton(), list(map(lambda step: Step.instance_of(graph, step).frame, plan.steps())), negate=plan.is_negated())

    def __init__(self, frame: Frame):
        self.frame = frame

    def name(self) -> str:
        if "NAME" in self.frame:
            return self.frame["NAME"].singleton()

    def is_negated(self) -> bool:
        if "NEGATE" in self.frame:
            return self.frame["NEGATE"].singleton()
        return False

    def select(self, varmap: VariableMap) -> bool:
        if self.is_default():
            return True

        if "SELECT" in self.frame:
            select = self.frame["SELECT"].singleton()
            if isinstance(select, Frame) and (select ^ "@EXE.BOOLEAN-STATEMENT" or select ^ "@EXE.MP-STATEMENT"):
                result = Statement.from_instance(select).run(StatementScope(), varmap)
                if self.is_negated():
                    result = not result
                return result
        return False

    def is_default(self):
        if "SELECT" in self.frame:
            select = self.frame["SELECT"].singleton()
            if select == Plan.DEFAULT:
                return True
        return False

    def steps(self) -> List['Step']:
        results = list(map(lambda s: Step(s), self.frame["HAS-STEP"]))
        results = sorted(results, key=lambda s: s.index())
        return results

    def executed(self) -> bool:
        for step in self.steps():
            if step.is_pending():
                return False
        return True

    def __eq__(self, other):
        if isinstance(other, Plan):
            return (self.frame == other.frame) or (
                self.frame["NAME"] == list(other.frame["NAME"]) and
                self.frame["NEGATE"] == list(other.frame["NEGATE"]) and
                self.__eqSELECT(other) and
                self.__eqSTEPS(other)
            )
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)

    def __eqSELECT(self, other: 'Plan'):
        if self.frame["SELECT"] == list(other.frame["SELECT"]):
            return True
        if self.frame["SELECT"] == Plan.DEFAULT or other.frame["SELECT"] == Plan.DEFAULT:
            return False

        s1 = list(map(lambda frame: Statement.from_instance(frame), self.frame["SELECT"]))
        s2 = list(map(lambda frame: Statement.from_instance(frame), other.frame["SELECT"]))

        return s1 == s2

    def __eqSTEPS(self, other: 'Plan'):
        if self.frame["HAS-STEP"] == list(other.frame["HAS-STEP"]):
            return True
        if len(self.frame["HAS-STEP"]) != len(other.frame["HAS-STEP"]):
            return False

        s1 = list(map(lambda frame: Step(frame), self.frame["HAS-STEP"]))
        s2 = list(map(lambda frame: Step(frame), other.frame["HAS-STEP"]))

        return s1 == s2


class Step(object):

    IDLE = "IDLE"

    @classmethod
    def build(cls, space: Space, index: int, perform: Union[Statement, Frame, str, List[Union[Statement, Frame, str]]]) -> 'Step':
        if not isinstance(perform, list):
            perform = [perform]
        perform = list(map(lambda p: p.frame if isinstance(p, Statement) else p, perform))

        frame = Frame("@" + space.name + ".STEP.?")
        frame["INDEX"] = index
        frame["PERFORM"] = perform
        frame["STATUS"] = Step.Status.PENDING

        return Step(frame)

    @classmethod
    def instance_of(cls, graph: Graph, step: Union[Frame, 'Step']) -> 'Step':

        if isinstance(step, Frame):
            step = Step(step)

        return Step.build(graph, step.index(), list(map(lambda stmt: stmt.resolve(), step.frame["PERFORM"])))

    class Status(Enum):
        PENDING = "PENDING"
        FINISHED = "FINISHED"

    def __init__(self, frame: Frame):
        self.frame = frame

    def index(self) -> int:
        return self.frame["INDEX"].singleton()

    def status(self) -> 'Step.Status':
        return self.frame["STATUS"].singleton()

    def is_pending(self) -> bool:
        return self.frame["STATUS"].singleton() == Step.Status.PENDING

    def is_finished(self) -> bool:
        return self.frame["STATUS"].singleton() == Step.Status.FINISHED

    def perform(self, varmap: VariableMap) -> StatementScope:
        scope = StatementScope()
        for statement in self.frame["PERFORM"]:
            statement = statement
            if statement == Step.IDLE:
                pass
            if isinstance(statement, Frame) and statement ^ "@EXE.STATEMENT":
                Statement.from_instance(statement).run(scope, varmap)

        for transient in scope.transients:
            transient.update_scope(lambda: self.is_pending())

        return scope

    def __eq__(self, other):
        if isinstance(other, Step):
            return self.frame == other.frame or (
                self.__eqPERFORM(other) and
                self.frame["STATUS"] == list(other.frame["STATUS"]) and
                self.frame["INDEX"] == list(other.frame["INDEX"])
            )
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)

    def __eqPERFORM(self, other: 'Step'):
        if self.frame["PERFORM"] == list(other.frame["PERFORM"]):
            return True
        if self.frame["PERFORM"] == Step.IDLE or other.frame["PERFORM"] == Step.IDLE:
            return False

        s1 = list(map(lambda frame: Statement.from_instance(frame), self.frame["PERFORM"]))
        s2 = list(map(lambda frame: Statement.from_instance(frame), other.frame["PERFORM"]))

        return s1 == s2


class Trigger(object):

    @classmethod
    def build(cls, space: Space, query: Query, definition: Union[str, Identifier, Frame, Goal]) -> 'Trigger':
        if isinstance(definition, str):
            definition = Frame(definition)
        if isinstance(definition, Goal):
            definition = definition.frame
        if isinstance(definition, Identifier):
            definition = Frame(definition.id)

        frame = Frame("@" + space.name + ".TRIGGER.?")
        frame["QUERY"] = query
        frame["DEFINITION"] = definition

        return Trigger(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def query(self) -> Query:
        return self.frame["QUERY"].singleton()

    def definition(self) -> Goal:
        return Goal(self.frame["DEFINITION"].singleton())

    def triggered_on(self) -> List[Frame]:
        return list(self.frame["TRIGGERED-ON"])

    def fire(self, agenda: [Frame, Agenda]):
        if isinstance(agenda, Frame):
            agenda = Agenda(agenda)

        results = self.query().start(graph)
        results = filter(lambda r: r not in self.frame["TRIGGERED-ON"], results)

        for r in results:
            agenda.add_goal(Goal.instance_of(self.frame.space(), self.definition(), [r]))
            self.frame["TRIGGERED-ON"] += r

    def __eq__(self, other):
        if isinstance(other, Trigger):
            return self.query() == other.query() and self.definition() == other.definition()
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class Condition(object):

    @classmethod
    def build(cls, space: Space, statements: List[Statement], status: Goal.Status, logic: 'Condition.Logic'=1, order: int=1, on: 'Condition.On'=None):
        frame = Frame("@" + space.name + ".CONDITION.?")
        frame["IF"] = list(map(lambda statement: statement.frame, statements))
        frame["LOGIC"] = logic
        frame["STATUS"] = status
        frame["ORDER"] = order

        if on is not None:
            frame["ON"] = on

        return Condition(frame)

    class On(Enum):
        EXECUTED = "EXECUTED"

    class Logic(Enum):
        AND = 1
        OR = 2
        NOR = 3
        NAND = 4
        NOT = 5

    def __init__(self, frame: Frame):
        self.frame = frame

        for statement in self.frame["IF"]:
            if not statement ^ "@EXE.BOOLEAN-STATEMENT":
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

    def on(self) -> 'Condition.On':
        if "ON" in self.frame:
            return self.frame["ON"].singleton()

    def assess(self, varmap: VariableMap) -> bool:
        if "ON" in self.frame:
            on = self.on()
            if on == Condition.On.EXECUTED:
                return Goal(varmap.frame).executed()

        if "IF" not in self.frame:
            return True

        results = map(lambda wc: self._assess_if(wc, varmap), self.frame["IF"])

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
        if not frame ^ "@EXE.BOOLEAN-STATEMENT":
            raise Exception("IF statement is not a BOOLEAN-STATEMENT.")
        return Statement.from_instance(frame).run(StatementScope(), varmap)

    def __eq__(self, other):
        if isinstance(other, Condition):
            return self.frame == other.frame or (
                self.__eqIF(other) and
                self.frame["LOGIC"] == list(other.frame["LOGIC"]) and
                self.frame["STATUS"] == list(other.frame["STATUS"]) and
                self.frame["ORDER"] == list(other.frame["ORDER"]) and
                self.frame["ON"] == list(other.frame["ON"])
            )
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)

    def __eqIF(self, other: 'Condition'):
        if self.frame["IF"] == other.frame["IF"]:
            return True

        s1 = list(map(lambda frame: Statement.from_instance(frame), self.frame["IF"]))
        s2 = list(map(lambda frame: Statement.from_instance(frame), other.frame["IF"]))

        return s1 == s2


class Decision(object):

    class Status(Enum):
        PENDING = "PENDING"
        SELECTED = "SELECTED"
        DECLINED = "DECLINED"
        BLOCKED = "BLOCKED"
        EXECUTING = "EXECUTING"
        FINISHED = "FINISHED"

    '''
    EXE.DECISION = {
      ISA           ^ONT.MENTAL-OBJECT;
      ON-GOAL       ^EXE.GOAL;
      ON-PLAN       ^EXE.PLAN;
      ON-STEP       ^EXE.STEP;
      HAS-OUTPUT*   ^EXE.XMR;
      HAS-PRIORITY? Literal(dbl);
      HAS-COST?     Literal(dbl);
      REQUIRES*     ^EXE.CAPABILITY;
      STATUS        Literal(str[PENDING | SELECTED | DECLINED | BLOCKED | EXECUTING | FINISHED]);
      HAS-EFFECTOR* ^EXE.EFFECTOR;
      HAS-CALLBACK* ^EXE.CALLBACK;
    }
    '''

    @classmethod
    # def build(cls, graph: Graph, goal: Union[str, Identifier, Frame, Goal], plan: Union[str, Identifier, Frame, Plan], step: Union[str, Identifier, Frame, Step]) -> 'Decision':
    def build(cls, space: Space, goal: Union[str, Identifier, Frame, Goal], plan: Union[str, Identifier, Frame, Plan], step: Union[str, Identifier, Frame, Step]) -> 'Decision':
        if isinstance(goal, Goal):
            goal = goal.frame
        if isinstance(plan, Plan):
            plan = plan.frame
        if isinstance(step, Step):
            step = step.frame

        # decision = graph.register("DECISION", isa="EXE.DECISION", generate_index=True)
        decision = Frame("@" + space.name + ".DECISION.?")
        decision["IS-A"] = Frame("@EXE.DECISION")
        decision["ON-GOAL"] = goal
        decision["ON-PLAN"] = plan
        decision["ON-STEP"] = step
        decision["STATUS"] = Decision.Status.PENDING.name

        return Decision(decision)

    def __init__(self, frame: Frame):
        self.frame = frame

    def goal(self) -> Goal:
        return Goal(self.frame["ON-GOAL"].singleton())

    def plan(self) -> Plan:
        return Plan(self.frame["ON-PLAN"].singleton())

    def step(self) -> Step:
        return Step(self.frame["ON-STEP"].singleton())

    def impasses(self) -> List[Goal]:
        return list(map(lambda i: Goal(i), self.frame["HAS-IMPASSE"]))

    def outputs(self) -> List['XMR']:
        from backend.models.output import XMR
        return list(map(lambda output: XMR(output), self.frame["HAS-OUTPUT"]))

    def expectations(self) -> List['Expectation']:
        return list(map(lambda expectation: Expectation(expectation), self.frame["HAS-EXPECTATION"]))

    def priority(self) -> Union[float, None]:
        if "HAS-PRIORITY" not in self.frame:
            return None
        return self.frame["HAS-PRIORITY"].singleton()

    def cost(self) -> Union[float, None]:
        if "HAS-COST" not in self.frame:
            return None
        return self.frame["HAS-COST"].singleton()

    def requires(self) -> List['Capability']:
        return list(map(lambda output: output.capability(), self.outputs()))

    def status(self) -> 'Decision.Status':
        if "STATUS" not in self.frame:
            return Decision.Status.PENDING
        status = self.frame["STATUS"].singleton()
        if isinstance(status, str):
            status = Decision.Status[status]

        return status

    def effectors(self) -> List['Effector']:
        from backend.models.effectors import Effector
        return list(self.frame["HAS-EFFECTOR"])

    def callbacks(self) -> List['Callback']:
        from backend.models.effectors import Callback
        return list(self.frame["HAS-CALLBACK"])

    def select(self):
        self.frame["STATUS"] = Decision.Status.SELECTED

    def decline(self):
        self.frame["STATUS"] = Decision.Status.DECLINED

    def inspect(self):
        self._generate_outputs()
        self._calculate_priority()
        self._calculate_cost()

    def _generate_outputs(self):
        try:
            scope = self.step().perform(self.goal())
            self.frame["HAS-OUTPUT"] = list(map(lambda output: output.frame, scope.outputs))
            self.frame["HAS-EXPECTATION"] = list(map(lambda expectation: Expectation.build(self.goal().frame.space(), Expectation.Status.PENDING, expectation).frame, scope.expectations))
        except AssertStatement.ImpasseException as e:
            for r in e.resolutions:
                impasse: Frame = r.run(StatementScope(), self.goal())
                self.frame["HAS-IMPASSE"] += impasse
                self.goal().frame["HAS-GOAL"] += impasse
            self.frame["STATUS"] = Decision.Status.BLOCKED

    def _calculate_priority(self):
        self.frame["HAS-PRIORITY"] = self.goal().priority()

    def _calculate_cost(self):
        self.frame["HAS-COST"] = self.goal().resources()

    def execute(self, agent: 'Agent', effectors: List['Effector']):
        from backend.models.effectors import Callback

        self.frame["STATUS"] = Decision.Status.EXECUTING

        for effector in effectors:
            self.frame["HAS-EFFECTOR"] += effector.frame

        for effector in effectors:
            callback = Callback.build(self.frame.space(), self, effector)
            self.frame["HAS-CALLBACK"] += callback.frame

            effector.on_capability().run(agent, effector.on_output(), callback)
            effector.on_output().frame["TIMESTAMP"] = time.time()

    def callback_received(self, callback: 'Callback'):
        self.frame["HAS-EFFECTOR"] -= callback.effector().frame
        self.frame["HAS-CALLBACK"] -= callback.frame

    def assess_impasses(self):
        self.frame["HAS-IMPASSE"] = list(map(lambda i: i.frame, filter(lambda i: not i.is_satisfied(), self.impasses())))

    def __eq__(self, other):
        if isinstance(other, Decision):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class Expectation(object):

    class Status(Enum):
        PENDING = "PENDING"
        EXPECTING = "EXPECTING"
        SATISFIED = "SATISFIED"

    @classmethod
    def build(cls, space: Space, status: 'Expectation.Status', condition: Union[str, Identifier, Frame, Statement]):
        if isinstance(condition, Statement):
            condition = condition.frame

        frame = Frame("@" + space.name + ".EXPECTATION.?")

        frame["STATUS"] = status
        frame["CONDITION"] = condition

        return Expectation(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def status(self) -> 'Expectation.Status':
        return self.frame["STATUS"].singleton()

    def condition(self) -> Statement:
        return Statement.from_instance(self.frame["CONDITION"].singleton())

    def assess(self, varmap: VariableMap):
        if self.condition().run(StatementScope(), varmap):
            self.frame["STATUS"] = Expectation.Status.SATISFIED
        else:
            self.frame["STATUS"] = Expectation.Status.PENDING

    def __eq__(self, other):
        if isinstance(other, Expectation):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class Effect(object):

    @classmethod
    def build(cls, space: Space, statements: List[Union[str, Identifier, Frame, Statement]]) -> 'Effect':
        statements = list(map(lambda s: Frame(s) if isinstance(s, str) else s, statements))
        statements = list(map(lambda s: s.frame if isinstance(s, Statement) else s, statements))
        statements = list(map(lambda s: Frame(s.id) if isinstance(s, Identifier) else s, statements))

        effect = Frame("@" + space.name + ".EFFECT.?").add_parent("@EXE.EFFECT")

        for statement in statements:
            effect["HAS-STATEMENT"] += statement

        return Effect(effect)

    def __init__(self, frame: Frame):
        self.frame = frame

    def statements(self) -> List[Statement]:
        return list(map(lambda s: Statement.from_instance(s), self.frame["HAS-STATEMENT"]))

    def apply(self, varmap: VariableMap):
        scope = StatementScope()

        for statement in self.statements():
            statement.run(scope, varmap)

    def __eq__(self, other):
        if isinstance(other, Effect):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)