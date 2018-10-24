from backend.models.graph import Frame, Graph, Identifier, Literal, Network

from enum import Enum
from typing import Union


# XMR is a Frame wrapper object for holding a node as a reference to a particular meaning representation, and resolving
# a graph from a network for that MR.  An example usage is holding a reference to a TMR as part of agent input
# and agenda processing.

class XMR(object):

    class Status(Enum):
        RECEIVED = "RECEIVED"
        ACKNOWLEDGED = "ACKNOWLEDGED"
        UNDERSTOOD = "UNDERSTOOD"
        IGNORED = "IGNORED"

    class Type(Enum):
        LANGUAGE = "LANGUAGE"
        VISUAL = "VISUAL"

    @classmethod
    def instance(cls, graph: Graph, refers_to: Union[str, Graph], isa: str="EXE.INPUT-TMR", status: Union[str, Status]=Status.RECEIVED, type: Union[str, Type]=Type.LANGUAGE, source: Union[str, Identifier, Frame]=None) -> 'XMR':

        if isinstance(refers_to, Graph):
            refers_to = refers_to._namespace

        if isinstance(status, XMR.Status):
            status = status.value

        if isinstance(type, XMR.Type):
            type = type.value

        if source is not None:
            if isinstance(source, str):
                source = Identifier.parse(source)
            if isinstance(source, Frame):
                source = source._identifier

        frame = graph.register("XMR", isa=isa, generate_index=True)
        frame["REFERS-TO-GRAPH"] = Literal(refers_to)
        frame["STATUS"] = Literal(status)
        frame["TYPE"] = Literal(type)

        if source is not None:
            frame["SOURCE"] = source

        return XMR(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def status(self) -> Status:
        status = self.frame["STATUS"].singleton()
        if isinstance(status, str):
            status = XMR.Status[status]
        return status

    def type(self) -> Type:
        type = self.frame["TYPE"].singleton()
        if isinstance(type, str):
            type = XMR.Type[type]
        return type

    def source(self) -> Frame:
        return self.frame["SOURCE"].singleton()

    def graph(self, network: Network) -> Graph:
        return network[self.frame["REFERS-TO-GRAPH"].singleton()]