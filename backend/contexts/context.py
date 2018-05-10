

class AgentContext(object):

    def __init__(self, agent):
        self.agent = agent
        self.heuristics = []

        self.prepare_static_knowledge()

    def prepare_static_knowledge(self):
        pass

    def process(self, tmr):
        for heuristic in self.heuristics:
            if heuristic(tmr):
                return