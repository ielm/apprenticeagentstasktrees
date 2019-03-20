# # from backend.agent import Agent
# from backend.models.agenda import Agenda, Goal, Trigger
# from backend.models.effectors import Capability
# from backend.models.grammar import Grammar
# # from backend.models.graph import Filler, Frame, Graph, Identifier, Literal, Network
# from backend.models.mps import AgentMethod, MPRegistry, OutputMethod
# # from backend.models.ontology import Ontology, OntologyFrame, OntologyFiller
# from backend.models.output import OutputXMRTemplate
# from backend.models.query import Query
# from backend.models.xmr import XMR
# from ontograph.Frame import Frame
from ontograph.Index import Identifier
# from ontograph.Space import Space
# from pkgutil import get_data
from typing import Any, List, Type, Union
#
#
# class Agent(object): pass
# class Literal(object): pass
# class Network(object): pass
# class Graph(object): pass
#
#
# class Bootstrap(object):
#
#     loaded = []
#
#     @classmethod
#     def bootstrap_script(cls, agent: Agent, script: str):
#         bootstraps = Grammar.parse(agent, script, start="bootstrap", agent=agent)
#         for bootstrap in bootstraps:
#             bootstrap()
#
#     @classmethod
#     def bootstrap_resource(cls, agent: Agent, package: str, file: str):
#         input: str = get_data(package, file).decode('ascii')
#         bootstraps = Grammar.parse(agent, input, start="bootstrap")
#         for bootstrap in bootstraps:
#             bootstrap()
#
#         Bootstrap.loaded.append(package + "." + file)
#
#     @classmethod
#     def list_resources(cls, package: str):
#         from pkg_resources import resource_listdir
#         return list(map(lambda f: (package, f), filter(lambda f: f.endswith(".knowledge") or f.endswith(".environment"), resource_listdir(package, ''))))
#
#
class BootstrapTriple(object):

    def __init__(self, slot: str, filler: Union[Identifier, Any], facet: str=None):
        self.slot = slot
        self.facet = facet
        self.filler = filler

    def __eq__(self, other):
        if isinstance(other, BootstrapTriple):
            return self.slot == other.slot and self.facet == other.facet and self.filler == other.filler
        return super().__eq__(other)
#
#
# # @DeprecationWarning
# # class BootstrapDeclareKnowledge(Bootstrap):
# #
# #     def __init__(self, space: Union[str, Space], name: str, index: Union[int, bool]=False, isa: Union[str, Identifier, List[Union[str, Identifier]]]=None, properties: Union[BootstrapTriple, List[BootstrapTriple]]=None):
# #         self.space = space
# #         self.name = name
# #         self.index = index
# #         self.isa = isa
# #         self.properties = properties
# #
# #         if self.isa is None:
# #             self.isa = []
# #         if not isinstance(self.isa, list):
# #             self.isa = [self.isa]
# #
# #         if self.properties is None:
# #             self.properties = []
# #         if not isinstance(self.properties, list):
# #             self.properties = [self.properties]
# #
# #     def __call__(self, *args, **kwargs):
# #         if isinstance(self.space, Space):
# #             self.space = self.space.name
# #
# #         id = ""
# #         if not isinstance(self.index, bool):
# #             id = "." + str(self.index)
# #         elif self.index:
# #             id = ".?"
# #
# #         frame = Frame("@" + self.space + "." + self.name + id)
# #
# #         for parent in self.isa:
# #             frame.add_parent(parent)
# #
# #         for property in self.properties:
# #             if property.facet is None:
# #                 frame[property.slot] += property.filler
# #             else:
# #                 frame[property.slot][property.facet] += property.filler
# #             # if isinstance(self.graph, Ontology):
# #             #     frame[property.slot] += OntologyFiller(property.filler, property.facet)
# #             # else:
# #             #     frame[property.slot] += property.filler
# #
# #     def __eq__(self, other):
# #         if isinstance(other, BootstrapDeclareKnowledge):
# #             return self.space == other.space and \
# #                     self.name == other.name and \
# #                     self.index == other.index and \
# #                     self.isa == other.isa and \
# #                     self.properties == other.properties
# #         return super().__eq__(other)
# #
# #
# # @DeprecationWarning
# # class BootstrapAppendKnowledge(Bootstrap):
# #
# #     def __init__(self, frame: Union[Frame, Identifier, str], properties: Union[BootstrapTriple, List[BootstrapTriple]]):
# #         self.frame = frame
# #         self.properties = properties
# #
# #         if not isinstance(self.properties, list):
# #             self.properties = [self.properties]
# #
# #     def __call__(self, *args, **kwargs):
# #         if isinstance(self.frame, str):
# #             self.frame = Frame(self.frame)
# #         if isinstance(self.frame, Identifier):
# #             self.frame = Frame(self.frame.id)
# #
# #         for property in self.properties:
# #             self.frame[property.slot][property.facet] += property.filler
# #             # if isinstance(self.frame, OntologyFrame):
# #             #     self.frame[property.slot] += OntologyFiller(property.filler, property.facet)
# #             # else:
# #             #     self.frame[property.slot] += property.filler
# #
# #     def __eq__(self, other):
# #         if isinstance(other, BootstrapAppendKnowledge):
# #             return self.frame == other.frame and \
# #                     self.properties == other.properties
# #         return super().__eq__(other)
# #
# #
# # @DeprecationWarning
# # class BootstrapRegisterMP(Bootstrap):
# #
# #     def __init__(self, mp: Type[Union[AgentMethod, OutputMethod]], name: str=None):
# #         self.mp = mp
# #         self.name = name
# #
# #     def __call__(self, *args, **kwargs):
# #         name = self.name if self.name is not None else self.mp.__name__
# #         MPRegistry.register(self.mp, name)
# #
# #     def __eq__(self, other):
# #         if isinstance(other, BootstrapRegisterMP):
# #             return self.mp.__name__ == other.mp.__name__ and self.name == other.name
# #         return super().__eq__(other)
# #
# #
# # @DeprecationWarning
# # class BoostrapGoal(Bootstrap):
# #
# #     def __init__(self, goal: Goal):
# #         self.goal = goal
# #
# #     def __call__(self, *args, **kwargs):
# #         return self.goal
# #
# #
# # @DeprecationWarning
# # class BootstrapAddTrigger(Bootstrap):
# #
# #     def __init__(self, agenda: Union[str, Identifier, Frame, Agenda], definition: Union[str, Identifier, Frame, Goal], query: Query):
# #         self.agenda = agenda
# #         self.definition = definition
# #         self.query = query
# #
# #     def __call__(self, *args, **kwargs):
# #         agenda = self.agenda
# #         if isinstance(agenda, str):
# #             agenda = Frame(agenda)
# #         if isinstance(agenda, Identifier):
# #             agenda = Frame(agenda.id)
# #         if isinstance(agenda, Agenda):
# #             agenda = agenda.frame
# #
# #         trigger = Trigger.build(agenda.space(), self.query, self.definition)
# #         Agenda(agenda).add_trigger(trigger)
# #
# #     def __eq__(self, other):
# #         if isinstance(other, BootstrapAddTrigger):
# #             return self.agenda == other.agenda and \
# #                     self.definition == other.definition and \
# #                     self.query == other.query
# #         return super().__eq__(other)
# #
# #
# # @DeprecationWarning
# # class BootstrapDefineOutputXMRTemplate(Bootstrap):
# #
# #     def __init__(self, name: str, type: XMR.Type, capability: Union[str, Identifier, Frame, Capability], params: List[str], root: Union[str, Identifier, Frame, None], frames: List[BootstrapDeclareKnowledge]):
# #         self.name = name
# #         self.type = type
# #         self.capability = capability
# #         self.params = params
# #         self.root = root
# #         self.frames = frames
# #
# #     def __call__(self, *args, **kwargs):
# #         template = OutputXMRTemplate.build(self.name, self.type, self.capability, self.params)
# #         if self.root is not None:
# #             r = self.root
# #             if isinstance(r, Frame):
# #                 r = r.id
# #             if isinstance(r, Identifier):
# #                 r = r.id
# #
# #             r = r.replace("@OUT", "@" + template.space.name)
# #
# #             r = Frame(r)
# #             template.set_root(r)
# #
# #
# #
# #             # if isinstance(r, str):
# #             #     r = Frame(r)
# #             # if isinstance(r, Identifier):
# #             #     r = Frame(r.id)
# #             # if r.space().name == "OUT":
# #             #     r.graph = template.graph._namespace
# #             # template.set_root(r)
# #
# #         for frame in self.frames:
# #             frame.space = template.space
# #             for triple in frame.properties:
# #                 if isinstance(triple.filler, Identifier):
# #                     triple.filler.id = triple.filler.id.replace("@OUT", "@" + template.space.name)
# #                     # if triple.filler.graph == "OUT":
# #                     #     triple.filler.graph = template.graph._namespace
# #
# #         for frame in self.frames:
# #             frame()
# #
# #     def __eq__(self, other):
# #         if isinstance(other, BootstrapDefineOutputXMRTemplate):
# #             return self.name == other.name and \
# #                 self.type == other.type and \
# #                 self.capability == other.capability and \
# #                 self.params == other.params and \
# #                 self.root == other.root and \
# #                 self.frames == other.frames
# #         return super().__eq__(other)