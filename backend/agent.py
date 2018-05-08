from backend.models.fr import FR
from backend.models.tmr import TMR


class Agent(object):

    def __init__(self):
        self.st_memory = FR()   # Short-term memory
        self.lt_memory = FR()   # Long-term memory

        self.input_memory = []

    def input(self, input):
        tmr = TMR(input)
        self.input_memory.append(tmr)
        self.st_memory.learn_tmr(tmr)