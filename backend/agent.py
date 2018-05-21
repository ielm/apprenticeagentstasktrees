from backend.contexts.context import AgentContext
from backend.contexts.LCTContext import LCTContext
from backend.models.fr import FR
from backend.models.tmr import TMR


class Agent(object):

    def __init__(self):
        self.st_memory = FR()   # Short-term memory
        self.lt_memory = FR()   # Long-term memory

        self.input_memory = []
        self.context = LCTContext(self)

    def input(self, input):
        tmr = TMR(input)
        self.input_memory.append(tmr)

        instructions = self.context.preprocess(tmr)
        if instructions[AgentContext.LEARN_ST_MEMORY]:
            self.st_memory.learn_tmr(tmr)
        if instructions[AgentContext.POST_PROCESS]:
            self.context.postprocess(tmr)
