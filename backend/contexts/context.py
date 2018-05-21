

class AgentContext(object):

    LEARN_ST_MEMORY = "LEARN_ST_MEMORY"
    POST_PROCESS = "POST_PROCESS"

    def __init__(self, agent):
        self.agent = agent
        self.pre_heuristics = []
        self.post_heuristics = []

        self.prepare_static_knowledge()

    def prepare_static_knowledge(self):
        pass

    def preprocess(self, tmr):
        instructions = {
            AgentContext.LEARN_ST_MEMORY: True,
            AgentContext.POST_PROCESS: True,
        }

        for heuristic in self.pre_heuristics:
            result = heuristic(tmr, instructions)
            if result is not None:
                return result

        return instructions

    def postprocess(self, tmr):
        for heuristic in self.post_heuristics:
            if heuristic(tmr):
                return