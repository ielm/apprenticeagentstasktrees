from backend.models.effectors import Capability
from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from backend.models.xmr import XMR
from typing import Any, List, Tuple, Union


class OutputXMRTemplate(object):

    @classmethod
    def build(cls, network: Network, name: str, type: XMR.Type, capability: Union[str, Identifier, Frame, Capability], params: List[str]) -> 'OutputXMRTemplate':
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

    @classmethod
    def list(cls, network: Network) -> List['OutputXMRTemplate']:
        templates = []
        for graph in network._storage.values():
            try:
                template = OutputXMRTemplate(graph)
                if template.graph._namespace.startswith("XMR-TEMPLATE#") and template.anchor() is not None:
                    templates.append(template)
            except: pass
        return templates

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

    def type(self) -> XMR.Type:
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
        if isinstance(root, str):
            root = Identifier.parse(root)

        anchor = self.anchor()
        anchor["ROOT"] = root

    def create(self, network: Network, graph: Graph, params: List[Any]) -> XMR:
        graph_id = "XMR#" + str(len(list(filter(lambda graph: graph.startswith("XMR#"), network._storage.keys()))) + 1)

        xmr_graph = network.register(graph_id)
        root = None
        if self.root() is not None:
            root = Identifier(graph_id, self.root()._identifier.name, self.root()._identifier.instance)
        anchor = XMR.instance(graph, xmr_graph, XMR.Signal.OUTPUT, self.type(), XMR.OutputStatus.PENDING, "SELF.ROBOT.1", root, self.capability())

        def materialize_transient_frame(param: Any):
            if isinstance(param, Identifier):
                param = param.resolve(None, network)
            if not isinstance(param, Frame):
                return param
            if not param ^ "EXE.TRANSIENT-FRAME":
                return param

            transient_frame: Frame = param
            parent = transient_frame["INSTANCE-OF"].singleton()

            materialized_id = Identifier(graph_id, parent._identifier.name)
            materialized_frame = xmr_graph.register(str(materialized_id), generate_index=True)

            for slot in transient_frame:
                for filler in transient_frame[slot]:
                    materialized_frame[slot] += filler

            return materialized_frame

        params = list(map(lambda param: materialize_transient_frame(param), params))

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