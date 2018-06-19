from backend.contexts.LCTContext import LCTContext
from backend.models.fr import FR
from backend.models.graph import Network
from backend.models.ontology import Ontology
from backend.models.tmr import TMR
from backend.utils.AgentLogger import AgentLogger


class Agent(object):

    def __init__(self, network: Network, ontology: Ontology=None):
        self.network = network
        self.ontology = ontology

        if self.ontology is None:
            raise Exception("NYI, Default Ontology Required")

        self.wo_memory = self.network.register(FR("WM", self.ontology))
        self.lt_memory = self.network.register(FR("LT", self.ontology))

        self.input_memory = []
        self.action_queue = []
        self.context = LCTContext(self)

        self._logger = AgentLogger()
        self.wo_memory.logger(self._logger)
        self.lt_memory.logger(self._logger)

    def logger(self, logger=None):
        if not logger is None:
            self._logger = logger
        return self._logger

    def input(self, input):
        tmr = self.network.register(TMR(input, ontology=self.ontology))
        self.input_memory.append(tmr)

        self._logger.log("Input: '" + tmr.sentence + "'")

        agenda = self.context.default_agenda()
        agenda.logger(self._logger)
        agenda.process(self, tmr)