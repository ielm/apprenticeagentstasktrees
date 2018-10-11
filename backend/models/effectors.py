from backend.models.agenda import Goal
from backend.models.graph import Frame, Graph, Literal
from backend.models.mps import MPRegistry
from backend.models.statement import CapabilityStatement, Statement, VariableMap
from enum import Enum
from typing import Callable, List, Union


class Effector(object):

    class Type(Enum):
        PHYSICAL = 1
        VERBAL = 2
        MENTAL = 3

    class Status(Enum):
        FREE = 1
        OPERATING = 2

    @classmethod
    def instance(cls, graph: Graph, type: Union[str, Type], capabilities: List[Union["Capability", Frame]]):
        if isinstance(type, str):
            type = Effector.Type[type]

        parent = "EFFECTOR"
        if type == Effector.Type.PHYSICAL:
            parent = "PHYSICAL-EFFECTOR"
        if type == Effector.Type.VERBAL:
            parent = "VERBAL-EFFECTOR"
        if type == Effector.Type.MENTAL:
            parent = "MENTAL-EFFECTOR"

        frame = graph.register(parent, isa="EXE." + parent, generate_index=True)

        for capability in capabilities:
            if isinstance(capability, Capability):
                capability = capability.frame
            frame["HAS-CAPABILITY"] += capability

        frame["STATUS"] = Effector.Status.FREE

        return Effector(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def type(self) -> Type:
        if self.frame ^ "EXE.PHYSICAL-EFFECTOR":
            return Effector.Type.PHYSICAL
        if self.frame ^ "EXE.VERBAL-EFFECTOR":
            return Effector.Type.VERBAL
        if self.frame ^ "EXE.MENTAL-EFFECTOR":
            return Effector.Type.MENTAL
        raise Exception("Unknown type for effector.")

    def is_free(self) -> bool:
        status = self.frame["STATUS"].singleton()
        return status == Effector.Status.FREE or status == Effector.Status.FREE.name

    def effecting(self) -> Goal:
        try:
            return Goal(self.frame["EFFECTING"].singleton())
        except Exception:
            return None

    def capabilities(self) -> List["Capability"]:
        return list(map(lambda c: Capability(c.resolve()), self.frame["HAS-CAPABILITY"]))

    def reserve(self, goal: Union[Frame, Goal], capability: Union[Frame, 'Capability']):
        if isinstance(goal, Goal):
            goal = goal.frame

        if isinstance(capability, Capability):
            capability = capability.frame

        self.frame["STATUS"] = Effector.Status.OPERATING
        self.frame["EFFECTING"] = goal
        self.frame["USES"] = capability
        goal["USES"] = [self.frame, capability]
        capability["USED-BY"] = self.frame

    def release(self):
        if self.is_free():
            return

        goal = self.frame["EFFECTING"].singleton()
        capability = self.frame["USES"].singleton()

        self.frame["STATUS"] = Effector.Status.FREE
        del self.frame["EFFECTING"]
        del self.frame["USES"]
        del goal["USES"]
        del capability["USED-BY"]

    def __eq__(self, other):
        if isinstance(other, Effector):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class Capability(object):

    @classmethod
    def instance(cls, graph: Graph, name: str, mp: Union[str, Callable]):
        frame = graph.register(name, isa="EXE.CAPABILITY")
        if not isinstance(mp, str):
            mp = mp.__name__

        frame["MP"] = Literal(mp)

        return Capability(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def run(self, *args, graph: Graph=None, callbacks: List[Union[Frame, CapabilityStatement]]=None, varmap: Union[Frame, VariableMap]=None, **kwargs) -> Callable:
        if graph is None:
            graph = self.frame._graph
        if callbacks is None:
            callbacks = []

        cb = Callback.instance(graph, varmap, callbacks, capability=self)
        kwargs["callback"] = cb

        return MPRegistry.run(self.mp_name(), *args, **kwargs)

    def mp_name(self) -> str:
        return self.frame["MP"].singleton()

    def used_by(self) -> Effector:
        if len(self.frame["USED-BY"]) == 0:
            return None
        return Effector(self.frame["USED-BY"].singleton())

    def __eq__(self, other):
        if isinstance(other, Capability):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class Callback(object):

    @classmethod
    def instance(cls, graph: Graph, varmap: Union[Frame, VariableMap], statements: List[Union[Frame, Statement]], capability: Union[Frame, Capability]):
        frame = graph.register("CALLBACK", isa="EXE.CALLBACK", generate_index=True)

        if isinstance(varmap, VariableMap):
            varmap = varmap.frame
        frame["VARMAP"] = varmap

        if isinstance(capability, Capability):
            capability = capability.frame
        frame["CAPABILITY"] = capability

        for statement in statements:
            if isinstance(statement, Statement):
                statement = statement.frame
            frame["STATEMENT"] += statement

        return Callback(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def run(self):
        varmap = self.varmap()
        statements = self.statements()
        for statement in statements:
            statement.run(varmap)

        capability = self.capability()
        if capability is None:
            return

        used_by = capability.used_by()
        if used_by is None:
            return

        used_by.release()

    def varmap(self) -> VariableMap:
        return VariableMap(self.frame["VARMAP"].singleton())

    def statements(self) -> List[Statement]:
        return list(map(lambda stmt: Statement.from_instance(stmt.resolve()), self.frame["STATEMENT"]))

    def capability(self) -> Capability:
        capability = self.frame["CAPABILITY"].singleton()
        if capability is None:
            return None

        return Capability(capability)