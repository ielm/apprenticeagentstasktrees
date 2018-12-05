from backend.models.effectors import Capability
from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from enum import Enum
from typing import Any, List, Tuple, Union


class OutputXMR(object):

    class Status(Enum):
        PENDING = "PENDING"
        ISSUED = "ISSUED"
        FINISHED = "FINISHED"

    @classmethod
    def build(cls, graph: Graph, type: 'OutputXMRTemplate.Type', capability: Union[str, Identifier, Frame, Capability], refers_to: str, root: Union[str, Identifier, Frame]=None) -> 'OutputXMR':
        xmr = graph.register("XMR", generate_index=True)

        if isinstance(capability, Capability):
            capability = capability.frame

        xmr["TYPE"] = type
        xmr["REQUIRES"] = capability
        xmr["REFERS-TO-GRAPH"] = Literal(refers_to)
        xmr["STATUS"] = OutputXMR.Status.PENDING

        if root is not None:
            xmr["ROOT"] = root

        return OutputXMR(xmr)

    def __init__(self, frame: Frame):
        self.frame = frame

    def type(self) -> 'OutputXMRTemplate.Type':
        return self.frame["TYPE"].singleton()

    def capability(self) -> Identifier:
        return self.frame["REQUIRES"].singleton()

    def status(self) -> 'OutputXMR.Status':
        return self.frame["STATUS"].singleton()

    def graph(self, network: Network) -> Graph:
        return network[self.frame["REFERS-TO-GRAPH"].singleton()]

    def root(self) -> Union[Frame, None]:
        if "ROOT" not in self.frame:
            return None
        return self.frame["ROOT"].singleton()


class OutputXMRTemplate(object):

    class Type(Enum):
        PHYSICAL = "PHYSICAL"
        MENTAL = "MENTAL"
        VERBAL = "VERBAL"

    @classmethod
    def build(cls, network: Network, name: str, type: 'OutputXMRTemplate.Type', capability: Union[str, Identifier, Frame, Capability], params: List[str]) -> 'OutputXMRTemplate':
        template_id = "XMR-TEMPLATE#" + str(len(list(filter(lambda graph: graph.startswith("XMR-TEMPLATE#"), network._storage.keys()))) + 1)

        graph = network.register(template_id)
        anchor = graph.register("TEMPLATE-ANCHOR", generate_index=True)

        if isinstance(capability, str):
            capability = Identifier.parse(capability)
        if isinstance(capability, Capability):
            capability = capability.frame

        params = list(map(lambda param: Literal(param) if not isinstance(param, Literal) else param, params))

        anchor["NAME"] = Literal(name)
        anchor["TYPE"] = type
        anchor["REQUIRES"] = capability
        anchor["PARAMS"] = params

        return OutputXMRTemplate(graph)

    @classmethod
    def lookup(cls, network: Network, name: str) -> Union['OutputXMRTemplate', None]:
        for graph in network._storage.values():
            try:
                template = OutputXMRTemplate(graph)
                if template.name() == name:
                    return template
            except: pass
        return None

    def __init__(self, graph: Graph):
        self.graph = graph

    def anchor(self) -> Frame:
        candidates = list(filter(lambda frame: frame._identifier.name == "TEMPLATE-ANCHOR", self.graph.values()))
        if len(candidates) != 1:
            raise Exception
        return candidates[0]

    def name(self) -> str:
        anchor = self.anchor()
        return anchor["NAME"].singleton()

    def type(self) -> 'OutputXMRTemplate.Type':
        anchor = self.anchor()
        return anchor["TYPE"].singleton()

    def capability(self) -> Identifier:
        anchor = self.anchor()
        return anchor["REQUIRES"].singleton()

    def params(self) -> List[str]:
        anchor = self.anchor()
        return list(map(lambda filler: filler.resolve(), anchor["PARAMS"]))

    def root(self) -> Union[Frame, None]:
        if "ROOT" not in self.anchor():
            return None
        return self.anchor()["ROOT"].singleton()

    def set_root(self, root: Union[str, Identifier, Frame]):
        anchor = self.anchor()
        anchor["ROOT"] = root

    def create(self, network: Network, graph: Graph, params: List[Any]) -> OutputXMR:
        graph_id = "XMR#" + str(len(list(filter(lambda graph: graph.startswith("XMR#"), network._storage.keys()))) + 1)

        xmr_graph = network.register(graph_id)
        root = None
        if self.root() is not None:
            root = Identifier(graph_id, self.root()._identifier.name, self.root()._identifier.instance)
        anchor = OutputXMR.build(graph, self.type(), self.capability(), graph_id, root)

        for frame in self.graph.values():
            if frame == self.anchor():
                continue

            modified_id = Identifier(graph_id, frame._identifier.name, frame._identifier.instance)
            copied = xmr_graph.register(str(modified_id))

            for slot in frame:
                for filler in frame[slot]:
                    value = filler.resolve()
                    if not isinstance(value, Frame):
                        if isinstance(value.value, str) and value.value.startswith("$"):
                            copied[slot] += params[self.params().index(value.value)]
                        else:
                            copied[slot] += value
                    elif value._identifier not in self.graph:
                        copied[slot] += value
                    else:
                        copied[slot] += Identifier(graph_id, value._identifier.name, value._identifier.instance)

        return anchor

    def __eq__(self, other):
        if isinstance(other, OutputXMRTemplate):
            return self.graph == other.graph
        if isinstance(other, Graph):
            return self.graph == other
        return super().__eq__(other)