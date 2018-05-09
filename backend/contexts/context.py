

class AgentContext(object):

    def __init__(self, agent):
        self.agent = agent
        self.heuristics = []

    def process(self, tmr):
        for heuristic in self.heuristics:
            heuristic(tmr)