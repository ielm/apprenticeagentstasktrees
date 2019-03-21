from backend.models.effectors import Capability
from enum import Enum
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Space import Space
from typing import Union

import time


# XMR is a Frame wrapper object for holding a node as a reference to a particular meaning representation, and resolving
# a graph from a network for that MR.  An example usage is holding a reference to a TMR as part of agent input
# and agenda processing.

class XMR(object):

    class Signal(Enum):
        INPUT = "INPUT"
        OUTPUT = "OUTPUT"

    class InputStatus(Enum):
        RECEIVED = "RECEIVED"
        ACKNOWLEDGED = "ACKNOWLEDGED"
        UNDERSTOOD = "UNDERSTOOD"
        IGNORED = "IGNORED"

    class OutputStatus(Enum):
        PENDING = "PENDING"
        ISSUED = "ISSUED"
        FINISHED = "FINISHED"

    class Type(Enum):
        ACTION = "ACTION"
        MENTAL = "MENTAL"
        LANGUAGE = "LANGUAGE"
        VISUAL = "VISUAL"

    @classmethod
    def from_instance(cls, frame: Frame) -> 'XMR':
        from backend.models.tmr import TMR
        from backend.models.vmr import VMR

        clazz = {
            "ACTION": AMR,
            "MENTAL": MMR,
            "LANGUAGE": TMR,
            "VISUAL": VMR,
        }[XMR(frame).type().name]

        return clazz(frame)

    @classmethod
    def instance(g, space: Space, refers_to: Union[str, Space], signal: Signal, type: Type, status: Union[InputStatus, OutputStatus], source: Union[str, Identifier, Frame], root: [str, Identifier, Frame], capability: [str, Identifier, Frame, Capability]=None) -> 'XMR':

        if isinstance(source, str):
            source = Frame(source)

        if isinstance(refers_to, Space):
            refers_to = refers_to.name

        if isinstance(capability, Capability):
            capability = capability.frame

        isa = {
            "ACTION": Frame("@EXE.AMR"),
            "MENTAL": Frame("@EXE.MMR"),
            "LANGUAGE": Frame("@EXE.TMR"),
            "VISUAL": Frame("@EXE.VMR"),
        }[type.name]

        frame = Frame("@" + space.name + ".XMR.?").add_parent(isa)

        frame["REFERS-TO-SPACE"] = refers_to
        frame["SIGNAL"] = signal
        frame["TYPE"] = type
        frame["STATUS"] = status
        frame["SOURCE"] = source
        frame["ROOT"] = root
        frame["TIMESTAMP"] = time.time()

        if capability is not None:
            frame["REQUIRES"] = capability

        return XMR.from_instance(frame)

    def __eq__(self, other):
        if isinstance(other, XMR):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other

        return super().__eq__(other)

    def __init__(self, frame: Frame):
        self.frame = frame

    def signal(self) -> Signal:
        return self.frame["SIGNAL"].singleton()

    def is_input(self) -> bool:
        return self.signal() == XMR.Signal.INPUT

    def is_output(self) -> bool:
        return self.signal() == XMR.Signal.OUTPUT

    def status(self) -> Union[InputStatus, OutputStatus]:
        status = self.frame["STATUS"].singleton()
        if isinstance(status, str):
            if status in [item.value for item in XMR.InputStatus]:
                status = XMR.InputStatus[status]
            if status in [item.value for item in XMR.OutputStatus]:
                status = XMR.OutputStatus[status]

        return status

    def type(self) -> Type:
        type = self.frame["TYPE"].singleton()
        if isinstance(type, str):
            type = XMR.Type[type]
        return type

    def source(self) -> Frame:
        return self.frame["SOURCE"].singleton()

    def space(self) -> Space:
        return Space(self.frame["REFERS-TO-SPACE"].singleton())

    def timestamp(self) -> float:
        return self.frame["TIMESTAMP"].singleton()

    def root(self) -> Frame:
        return self.frame["ROOT"].singleton()

    def capability(self) -> Capability:
        return Capability(self.frame["REQUIRES"].singleton())

    def set_status(self, status: Union[InputStatus, OutputStatus]):
        self.frame["STATUS"] = status

    def render(self) -> str:
        return self.frame.id


class AMR(XMR):

    def render(self):
        try:
            from backend import agent
            if self.source().id != agent.identity.id:
                return super().render()

            action = Identifier.parse(self.root().id)[1].upper()
            theme = self.root()["THEME"].singleton().id

            return "I am taking the " + action + "(" + theme + ") action."

        except: return super().render()


class MMR(XMR):

    def render(self):
        try:
            from backend import agent
            if Identifier.parse(self.root().id)[1] != "INIT-GOAL":
                return super().render()

            if self.source().id != agent.identity.id:
                return super().render()

            from backend.models.agenda import Goal

            goal = self.root()["THEME"].singleton()
            goal = Goal(goal).name()

            return "I am adding the " + goal + " goal."

        except: return super().render()