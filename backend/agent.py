from backend.contexts.context import AgentContext
from backend.contexts.LCTContext import LCTContext
from backend.models.fr import FR
from backend.models.tmr import TMR
from backend.utils.AgentLogger import AgentLogger


class Agent(object):

    def __init__(self):
        self.st_memory = FR(name="Short-term Memory", namespace="ST")
        self.lt_memory = FR(name="Long-term Memory", namespace="LT")

        self.input_memory = []
        self.context = LCTContext(self)

        self._logger = AgentLogger()
        self.context.logger(self._logger)
        self.st_memory.logger(self._logger)
        self.lt_memory.logger(self._logger)

    def logger(self, logger=None):
        if not logger is None:
            self._logger = logger
        return self._logger

    def input(self, input):
        tmr = TMR(input)
        self.input_memory.append(tmr)

        self._logger.log("Agent input: '" + tmr.sentence + "'")
        self._logger.indent()

        instructions = self.context.preprocess(tmr)
        if instructions[AgentContext.LEARN_ST_MEMORY]:
            self.st_memory.learn_tmr(tmr)
        if instructions[AgentContext.POST_PROCESS]:
            self.context.postprocess(tmr)

        self._logger.unindent()
