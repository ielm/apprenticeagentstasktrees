from backend.agent import Agent
from backend.models.agenda import Goal
from backend.models.grammar import Grammar
from backend.models.graph import Filler, Frame, Identifier, Literal, Network
from pkgutil import get_data
from typing import Union


class Bootstrap(object):

    @classmethod
    def bootstrap_resource(cls, agent: Agent, package: str, file: str):
        input: str = get_data(package, file).decode('ascii')
        bootstraps = Grammar.parse(agent, input, start="bootstrap", agent=agent)
        for bootstrap in bootstraps:
            bootstrap()


class BootstrapKnowledge(Bootstrap):

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
        if isinstance(other, BootstrapKnowledge):
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