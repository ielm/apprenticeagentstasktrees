from backend.utils.AgentLogger import CachedAgentLogger


class AgentContext(object):

    LEARN_WO_MEMORY = "LEARN_WO_MEMORY"
    POST_PROCESS = "POST_PROCESS"

    def __init__(self, agent):
        self.agent = agent

        self.prepare_static_knowledge()

    def prepare_static_knowledge(self):
        pass

    def default_agenda(self):
        raise Exception("Context.default_agenda must be implemented in subclasses.")


class HeuristicException(Exception):
    pass


class AgendaProcessor(object):

    def __init__(self, parent=None):
        self.parent = parent
        self._logger = None
        self.subprocesses = list()

    def log(self, message):
        if not self._logger:
            return

        self._logger.log(message)

    def logger(self, logger=None):
        if not logger is None:
            self._logger = logger

            for p in self.subprocesses:
                p.logger(logger=self._logger)

        return self._logger

    def _logic(self, agent, tmr):
        raise Exception("AgentProcessor._logic must be implemented in subclasses.")

    def add_subprocess(self, subprocess):
        subprocess.parent = self
        self.subprocesses.append(subprocess)

        return self

    def process(self, agent, tmr):
        try:
            self._logic(agent, tmr)
            self.log("+ " + self.__class__.__name__)
        except HeuristicException:
            self.log("x " + self.__class__.__name__)

        if self._logger is not None:
            self._logger.indent()

        while len(self.subprocesses) > 0:
            p = self.subprocesses[0]
            self.subprocesses = self.subprocesses[1:]
            p.process(agent, tmr)

        if self._logger is not None:
            self._logger.unindent()

    def halt_siblings(self):
        self.parent.subprocesses = []


class RootAgendaProcessor(AgendaProcessor):
    def _logic(self, agent, tmr):
        pass


class FRResolutionAgendaProcessor(AgendaProcessor):
    def _logic(self, agent, tmr):
        backup_logger = agent.wo_memory.logger()

        self.cached_logger = CachedAgentLogger()
        self.cached_logger.enable()
        agent.wo_memory.logger(logger=self.cached_logger)
        agent.wo_memory.learn_tmr(tmr)

        agent.wo_memory.logger(logger=backup_logger)

    def log(self, message):
        super().log(message)
        if self.cached_logger:
            self.logger().indent()
            for message in self.cached_logger._cache:
                super().log(message)
            self.logger().unindent()
            self.cached_logger = None
