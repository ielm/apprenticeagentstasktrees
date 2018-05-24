from backend.contexts.context import AgentContext
from backend.contexts.LCTContext import LCTContext
from backend.models.fr import FR
from backend.models.tmr import TMR
from backend.utils.AgentLogger import AgentLogger


class Agent(object):

    def __init__(self):
        self.wo_memory = FR(name="Working Memory", namespace="WM")
        self.lt_memory = FR(name="Long-term Memory", namespace="LT")

        self.input_memory = []
        self.context = LCTContext(self)

        self._logger = AgentLogger()
        self.wo_memory.logger(self._logger)
        self.lt_memory.logger(self._logger)

    def logger(self, logger=None):
        if not logger is None:
            self._logger = logger
        return self._logger

    def input(self, input):
        tmr = TMR(input)
        self.input_memory.append(tmr)

        self._logger.log("Input: '" + tmr.sentence + "'")

        agenda = self.context.default_agenda()
        agenda.logger(self._logger)
        agenda.process(self, tmr)
