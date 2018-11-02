from backend.agent import Agent
from backend.models.agenda import Goal
from backend.models.grammar import Grammar
from backend.models.graph import Filler, Frame, Graph, Identifier, Literal, Network
from backend.models.mps import AgentMethod, MPRegistry
from backend.models.ontology import Ontology, OntologyFrame, OntologyFiller
from pkgutil import get_data
from typing import Callable, List, Type, Union


class Bootstrap(object):

    loaded = []

    @classmethod
    def bootstrap_script(cls, agent: Agent, script: str):
        bootstraps = Grammar.parse(agent, script, start="bootstrap", agent=agent)
        for bootstrap in bootstraps:
            bootstrap()

    @classmethod
    def bootstrap_resource(cls, agent: Agent, package: str, file: str):
        input: str = get_data(package, file).decode('ascii')
        bootstraps = Grammar.parse(agent, input, start="bootstrap", agent=agent)
        for bootstrap in bootstraps:
            bootstrap()

        Bootstrap.loaded.append(package + "." + file)

    @classmethod
    def list_resources(cls, package: str):
        from pkg_resources import resource_listdir
        return list(map(lambda f: (package, f), filter(lambda f: f.endswith(".knowledge") or f.endswith(".aa") or f.endswith(".mps"), resource_listdir(package, ''))))


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

    def __init__(self, network: Network, frame: Union[Frame, Identifier, str], properties: Union[BootstrapTriple, List[BootstrapTriple]]):
        self.network = network
        self.frame = frame
        self.properties = properties

        if not isinstance(self.properties, list):
            self.properties = [self.properties]

    def __call__(self, *args, **kwargs):
        if isinstance(self.frame, str):
            self.frame = self.network.lookup(self.frame)
        if isinstance(self.frame, Identifier):
            self.frame = self.network.lookup(self.frame)

        for property in self.properties:
            if isinstance(self.frame, OntologyFrame):
                self.frame[property.slot] += OntologyFiller(property.filler, property.facet)
            else:
                self.frame[property.slot] += property.filler

    def __eq__(self, other):
        if isinstance(other, BootstrapAppendKnowledge):
            return self.network == other.network and \
                    self.frame == other.frame and \
                    self.properties == other.properties
        return super().__eq__(other)


class BootstrapRegisterMP(Bootstrap):

    def __init__(self, mp: Type[AgentMethod], name: str=None):
        self.mp = mp
        self.name = name

    def __call__(self, *args, **kwargs):
        name = self.name if self.name is not None else self.mp.__name__
        MPRegistry.register(self.mp, name)

    def __eq__(self, other):
        if isinstance(other, BootstrapRegisterMP):
            return self.mp.__name__ == other.mp.__name__ and self.name == other.name
        return super().__eq__(other)


class BoostrapGoal(Bootstrap):

    def __init__(self, goal: Goal):
        self.goal = goal

    def __call__(self, *args, **kwargs):
        return self.goal