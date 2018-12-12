from backend.models.agenda import Decision
from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from backend.models.mps import MPRegistry
from enum import Enum
from typing import Callable, List, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.agent import Agent
    from backend.models.output import OutputXMR


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

    def capabilities(self) -> List["Capability"]:
        return list(map(lambda c: Capability(c.resolve()), self.frame["HAS-CAPABILITY"]))

    def on_decision(self) -> Union[Decision, None]:
        if "ON-DECISION" not in self.frame:
            return None
        return Decision(self.frame["ON-DECISION"].singleton())

    def on_output(self) -> Union['OutputXMR', None]:
        from backend.models.output import OutputXMR
        if "ON-OUTPUT" not in self.frame:
            return None
        return OutputXMR(self.frame["ON-OUTPUT"].singleton())

    def on_capability(self) -> Union['Capability', None]:
        if "ON-CAPABILITY" not in self.frame:
            return None
        return Capability(self.frame["ON-CAPABILITY"].singleton())

    def reserve(self, decision: Union[str, Identifier, Frame, Decision], output: Union[str, Identifier, Frame, 'OutputXMR'], capability: Union[str, Identifier, Frame, 'Capability']):
        from backend.models.output import OutputXMR

        if isinstance(decision, Decision):
            decision = decision.frame

        if isinstance(output, OutputXMR):
            output = output.frame

        if isinstance(capability, Capability):
            capability = capability.frame

        self.frame["STATUS"] = Effector.Status.OPERATING
        self.frame["ON-DECISION"] = decision
        self.frame["ON-OUTPUT"] = output
        self.frame["ON-CAPABILITY"] = capability

    def release(self):
        self.frame["STATUS"] = Effector.Status.FREE
        del self.frame["ON-DECISION"]
        del self.frame["ON-OUTPUT"]
        del self.frame["ON-CAPABILITY"]

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

    def run(self, agent: 'Agent', output: 'OutputXMR', callback: 'Callback'):
        MPRegistry.output(self.mp_name(), agent, output, callback)

    def mp_name(self) -> str:
        return self.frame["MP"].singleton()

    def __eq__(self, other):
        if isinstance(other, Capability):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class Callback(object):

    @classmethod
    def build(cls, graph: Graph, decision: Union[str, Identifier, Frame, Decision], effector: Union[str, Identifier, Frame, Effector]) -> 'Callback':
        if isinstance(decision, Decision):
            decision = decision.frame

        if isinstance(effector, Effector):
            effector = effector.frame

        callback = graph.register("CALLBACK", isa="EXE.CALLBACK", generate_index=True)
        callback["FOR-DECISION"] = decision
        callback["FOR-EFFECTOR"] = effector

        return Callback(callback)

    def __init__(self, frame: Frame):
        self.frame = frame

    def decision(self) -> Decision:
        return Decision(self.frame["FOR-DECISION"].singleton())

    def effector(self) -> Effector:
        return Effector(self.frame["FOR-EFFECTOR"].singleton())

    def received(self):
        self.effector().release()
        self.decision().callback_received(self)
        del self.frame._graph[str(self.frame._identifier)]

    def __eq__(self, other):
        if isinstance(other, Callback):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)