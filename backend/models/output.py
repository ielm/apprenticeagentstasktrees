from backend.models.effectors import Capability
from backend.models.xmr import XMR
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Space import Space
from typing import Any, List, Union


class OutputXMRTemplate(object):

    @classmethod
    def build(cls, name: str, type: XMR.Type, capability: Union[str, Identifier, Frame, Capability], params: List[str]) -> 'OutputXMRTemplate':
        spaces = filter(lambda space: space.name.startswith("XMR-TEMPLATE#"), graph)
        spaces = list(map(lambda space: int(space.name.replace("XMR-TEMPLATE#", "")), spaces))

        template_id = "XMR-TEMPLATE#" + str(max(spaces) + 1 if len(spaces) > 0 else 1)

        space = Space(template_id)
        anchor = Frame("@" + space.name + ".TEMPLATE-ANCHOR.?").add_parent("@EXE.TEMPLATE-ANCHOR")

        if isinstance(capability, str):
            capability = Frame(capability)
        if isinstance(capability, Capability):
            capability = capability.frame
        if isinstance(capability, Identifier):
            capability = Frame(capability.id)

        anchor["NAME"] = name
        anchor["TYPE"] = type
        anchor["REQUIRES"] = capability
        anchor["PARAMS"] = params

        return OutputXMRTemplate(space)

    @classmethod
    def lookup(cls, name: str) -> Union['OutputXMRTemplate', None]:
        for space in graph:
            try:
                template = OutputXMRTemplate(space)
                if template.name() == name:
                    return template
            except: pass
        return None

    @classmethod
    def list(cls) -> List['OutputXMRTemplate']:
        templates = []
        for space in graph:
            try:
                template = OutputXMRTemplate(space)
                if template.space.name.startswith("XMR-TEMPLATE#") and template.anchor() is not None:
                    templates.append(template)
            except: pass
        return templates

    def __init__(self, space: Space):
        self.space = space

    def anchor(self) -> Frame:
        if self.space == graph.ontology():
            raise Exception

        from ontograph.Query import AndComparator, InSpaceComparator, IsAComparator, Query
        candidates = list(Query(AndComparator([InSpaceComparator(self.space), IsAComparator("@EXE.TEMPLATE-ANCHOR")])).start())
        if len(candidates) != 1:
            raise Exception
        return candidates[0]

    def name(self) -> str:
        anchor = self.anchor()
        return anchor["NAME"].singleton()

    def type(self) -> XMR.Type:
        anchor = self.anchor()
        return anchor["TYPE"].singleton()

    def capability(self) -> Capability:
        anchor = self.anchor()
        return Capability(anchor["REQUIRES"].singleton())

    def params(self) -> List[str]:
        anchor = self.anchor()
        return list(anchor["PARAMS"])

    def root(self) -> Union[Frame, None]:
        if "ROOT" not in self.anchor():
            return None
        return self.anchor()["ROOT"].singleton()

    def set_root(self, root: Union[str, Identifier, Frame]):
        if isinstance(root, str):
            root = Identifier.parse(root)

        anchor = self.anchor()
        anchor["ROOT"] = root

    def create(self, space: Space, params: List[Any]) -> XMR:
        spaces = filter(lambda space: space.name.startswith("XMR#"), graph)
        spaces = list(map(lambda space: int(space.name.replace("XMR#", "")), spaces))

        graph_id = "XMR#" + str(max(spaces) + 1 if len(spaces) > 0 else 1)

        xmr_graph = Space(graph_id)
        root = None
        if self.root() is not None:
            root = Identifier(self.root().id.replace("@" + self.root().space().name, "@" + graph_id))
        anchor = XMR.instance(space, xmr_graph, XMR.Signal.OUTPUT, self.type(), XMR.OutputStatus.PENDING, "@SELF.ROBOT.1", root, self.capability())

        def materialize_transient_frame(param: Any):
            if isinstance(param, Identifier):
                param = Frame(param.id)
            if not isinstance(param, Frame):
                return param
            if not param ^ "@EXE.TRANSIENT-FRAME":
                return param

            transient_frame: Frame = param
            parent = transient_frame["INSTANCE-OF"].singleton()

            materialized_id = "@" + graph_id + "." + Identifier.parse(parent.id)[1] + ".?"
            materialized_frame = Frame(materialized_id)

            for slot in transient_frame:
                for filler in slot:
                    materialized_frame[slot.property] += filler

            return materialized_frame

        params = list(map(lambda param: materialize_transient_frame(param), params))

        for frame in self.space:
            if frame == self.anchor():
                continue

            modified_id = frame.id.replace(frame.space().name, graph_id)
            copied = Frame(modified_id)

            for slot in frame:
                for filler in slot:
                    if not isinstance(filler, Frame):
                        if isinstance(filler, str) and filler.startswith("$"):
                            copied[slot.property] += params[self.params().index(filler)]
                        else:
                            copied[slot.property] += filler
                    elif filler not in self.space:
                        copied[slot.property] += filler
                    else:
                        copied[slot.property] += Frame(filler.id.replace(filler.space().name, graph_id))

        return anchor

    def __eq__(self, other):
        if isinstance(other, OutputXMRTemplate):
            return self.space == other.space
        if isinstance(other, Space):
            return self.space == other
        return super().__eq__(other)