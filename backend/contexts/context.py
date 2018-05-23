from backend.utils.AgentLogger import AgentLogger


class AgentContext(object):

    LEARN_ST_MEMORY = "LEARN_ST_MEMORY"
    POST_PROCESS = "POST_PROCESS"

    def __init__(self, agent):
        self._logger = AgentLogger()

        self.agent = agent
        self.pre_heuristics = []
        self.post_heuristics = []

        self.prepare_static_knowledge()

    def logger(self, logger=None):
        if not logger is None:
            self._logger = logger
        return self._logger

    def prepare_static_knowledge(self):
        pass

    def preprocess(self, tmr):
        instructions = {
            AgentContext.LEARN_ST_MEMORY: True,
            AgentContext.POST_PROCESS: True,
        }

        for heuristic in self.pre_heuristics:
            result = self._preprocess_log_wrapper(heuristic, tmr, instructions)
            if result is not None:
                break

        return instructions

    def postprocess(self, tmr):
        for heuristic in self.post_heuristics:
            if self._postprocess_log_wrapper(heuristic, tmr):
                return

    def _preprocess_log_wrapper(self, preprocess_heuristic, tmr, instructions):
        result = preprocess_heuristic(tmr, instructions)
        if result is not None:
            self._logger.log("matched PRE heuristic '" + preprocess_heuristic.__name__ + "' with instructions " + str(instructions))

        return result

    def _postprocess_log_wrapper(self, postprocess_heuristic, tmr):
        result = postprocess_heuristic(tmr)
        if result:
            self._logger.log("matched POST heuristic '" + postprocess_heuristic.__name__ + "'")

        return result