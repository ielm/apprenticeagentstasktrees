from backend.agent import Agent
from backend.models.agenda import Goal
from backend.models.grammar import Grammar
from backend.models.graph import Filler, Frame, Graph, Identifier, Literal, Network
from backend.models.ontology import Ontology, OntologyFiller
from pkgutil import get_data
from typing import List, Union


class Bootstrap(object):

    @classmethod
    def bootstrap_resource(cls, agent: Agent, package: str, file: str):
        input: str = get_data(package, file).decode('ascii')
        bootstraps = Grammar.parse(agent, input, start="bootstrap", agent=agent)
        for bootstrap in bootstraps:
            bootstrap()


class BootstrapTriple(object):

    def __init__(self, slot: str, filler: Union[Identifier, Literal], facet: str=None):
        self.slot = slot
        self.facet = facet
        self.filler = filler

    def __eq__(self, other):
        if isinstance(other, BootstrapTriple):
            return self.slot == other.slot and self.facet == other.facet and self.filler == other.filler
        return super().__eq__(other)


class BootstrapDeclareKnowledge(Bootstrap):

    def __init__(self, network: Network, graph: Union[str, Graph], name: str, index: Union[int, bool]=False, isa: Union[str, Identifier, List[Union[str, Identifier]]]=None, properties: Union[BootstrapTriple, List[BootstrapTriple]]=None):
        self.network = network
        self.graph = graph
        self.name = name
        self.index = index
        self.isa = isa
        self.properties = properties

        if self.isa is None:
            self.isa = []
        if not isinstance(self.isa, list):
            self.isa = [self.isa]

        if self.properties is None:
            self.properties = []
        if not isinstance(self.properties, list):
            self.properties = [self.properties]

    def __call__(self, *args, **kwargs):
        if isinstance(self.graph, str):
            self.graph = self.network[self.graph]

        id = self.name
        if not isinstance(self.index, bool):
            id = id + "." + str(self.index)

        generate_index = self.index if isinstance(self.index, bool) else False

        frame = self.graph.register(id, isa=self.isa, generate_index=generate_index)
        for property in self.properties:
            if isinstance(self.graph, Ontology):
                frame[property.slot] += OntologyFiller(property.filler, property.facet)
            else:
                frame[property.slot] += property.filler

    def __eq__(self, other):
        if isinstance(other, BootstrapDeclareKnowledge):
            return self.network == other.network and \
                    self.graph == other.graph and \
                    self.name == other.name and \
                    self.index == other.index and \
                    self.isa == other.isa and \
                    self.properties == other.properties
        return super().__eq__(other)


class BootstrapAppendKnowledge(Bootstrap):

    def __init__(self, network: Network, frame: Union[Frame, Identifier, str], slot: str, filler: Union[Filler, Identifier, Literal]):
        self.network = network
        self.frame = frame
        self.slot = slot
        self.filler = filler

    def __call__(self, *args, **kwargs):
        if isinstance(self.frame, str):
            self.frame = Identifier.parse(self.frame)
        if isinstance(self.frame, Identifier):
            self.frame = self.network.lookup(self.frame)

        if isinstance(self.filler, Identifier):
            self.filler = Filler(self.filler)
        if isinstance(self.filler, Literal):
            self.filler = Filler(self.filler)

        self.frame[self.slot] += self.filler

    def __eq__(self, other):
        if isinstance(other, BootstrapAppendKnowledge):
            return \
                self.network == other.network and \
                self.frame == other.frame and \
                self.slot == other.slot and \
                self.filler == other.filler
        return super().__eq__(other)


class BoostrapGoal(Bootstrap):

    def __init__(self, goal: Goal):
        self.goal = goal

    def __call__(self, *args, **kwargs):
        return self.goal