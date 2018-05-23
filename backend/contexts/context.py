from backend.utils.AgentLogger import AgentLogger


class AgentContext(object):

    LEARN_ST_MEMORY = "LEARN_ST_MEMORY"
    POST_PROCESS = "POST_PROCESS"

    def __init__(self, agent):
        self._logger = AgentLogger()

        self.agent = agent
        self.pre_heuristics = []
        self.post_heuristics = PostHeuristicsProcessor(None)

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
        self.post_heuristics.process(tmr, self._logger)

    def _preprocess_log_wrapper(self, preprocess_heuristic, tmr, instructions):
        result = preprocess_heuristic(tmr, instructions)
        if result is not None:
            self._logger.log("matched PRE heuristic '" + preprocess_heuristic.__name__ + "' with instructions " + str(instructions))

        return result


class PostHeuristicsProcessor(object):

    def __init__(self, heuristic, trigger=None, halt=None, subheuristics=list()):
        self.heuristic = heuristic                  # The heuristic to run
        self.trigger = trigger                      # The returned value from self.heuristic to match in order to run sub-heuristics
                                                    # (If self.trigger == None, sub-heuristics are run regardless of returned value)
        self.halt = halt                            # The halting condition for sub-heuristics; the first sub-heuristic to match
                                                    # will stop all others from running; again, None means no halting can happen
        self.subheuristics = list(subheuristics)    # The ordered list of subheuristics to run (must be PostHeuristicsProcessor type)

    def add_subheuristic(self, post_heuristics_processor):
        self.subheuristics.append(post_heuristics_processor)
        return self

    def process(self, tmr, logger):
        result = self.heuristic(tmr) if self.heuristic is not None else None
        if result is not None:
            logger.log("POST heuristic '" + self.heuristic.__name__ + "' = " + str(result))
            logger.indent()

        if self.trigger is None or self.trigger == result:
            for sub in self.subheuristics:
                sub_result = sub.process(tmr, logger)
                if sub_result is not None and sub_result == self.halt:
                    break

        if result is not None:
            logger.unindent()

        return result