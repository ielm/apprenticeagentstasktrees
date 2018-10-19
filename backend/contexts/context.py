from backend.heuristics.fr_heuristics import FRResolutionHeuristic
from backend.utils.AgentLogger import CachedAgentLogger


class AgentContext(object):
    """
    Agent Context
    """

    LEARN_WO_MEMORY = "LEARN_WO_MEMORY"
    POST_PROCESS = "POST_PROCESS"

    def __init__(self, agent):
        """
        Initialize Agent Context Template

        :param agent: Agent
        """
        self.agent = agent

        # self.prepare_static_knowledge()

    def prepare_static_knowledge(self):
        """
        Prepare Static Knowledge Template
        """
        pass

    def default_understanding(self):
        """
        Default Understanding Template
        """
        raise Exception("Context.default_understanding must be implemented in subclasses.")


class HeuristicException(Exception):
    pass


class UnderstandingProcessor(object):
    """
    Understanding Processor
    """

    def __init__(self, parent=None):
        """

        :param parent: Parent
        """
        self.parent = parent
        self._logger = None
        self.subprocesses = list()

    def log(self, message):
        """

        :param message: Message to log
        :return:
        """
        if not self._logger:
            return

        self._logger.log(message)

    def logger(self, logger=None):
        """

        :param logger: Agent Logger
        :return:
        """
        if not logger is None:
            self._logger = logger

            for p in self.subprocesses:
                p.logger(logger=self._logger)

        return self._logger

    def _logic(self, agent, tmr):
        raise Exception("UnderstandingProcessor._logic must be implemented in subclasses.")

    def add_subprocess(self, subprocess):
        """
        Adds subprocess to Understanding Processor

        :param subprocess: Subprocess to add
        :return: self
        """
        subprocess.parent = self
        self.subprocesses.append(subprocess)

        return self

    def process(self, agent, tmr):
        """
        Process input with Understanding Processor

        :param agent: Agent
        :param tmr: TMR to process
        """
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
        """
        Halts sibling processors

        :return:
        """
        if self.parent is None:
            return

        self.parent.subprocesses = []

    def reassign_siblings(self, siblings):
        """
        Reassign siblings to parent

        :param siblings:
        :return:
        """
        if self.parent is None:
            return

        self.parent.subprocesses = siblings
        for p in self.parent.subprocesses:
            p.logger(logger=self.parent.logger())


class RootUnderstandingProcessor(UnderstandingProcessor):
    """
    Root Understanding Processor
    """

    def _logic(self, agent, tmr):
        pass


class FRResolutionUnderstandingProcessor(UnderstandingProcessor):
    """
    Fact Repository Resolution Understanding Processor
    """

    def _logic(self, agent, tmr):
        """
        FR Resolution processor logic funcrion

        :param agent: Agent
        :param tmr: TMR to process
        """
        backup_logger = agent.wo_memory.logger()

        self.cached_logger = CachedAgentLogger()
        self.cached_logger.enable()

        agent.wo_memory.logger(logger=self.cached_logger)
        agent.wo_memory.learn_tmr(tmr)
        agent.wo_memory.logger(logger=backup_logger)

    def log(self, message):
        """
        Logs a message

        :param message: Message to log
        """
        super().log(message)
        if self.cached_logger:
            self.logger().indent()
            for message in self.cached_logger._cache:
                super().log(message)
            self.logger().unindent()
            self.cached_logger = None


class ContextBasedFRResolutionHeuristic(FRResolutionHeuristic):

    def __init__(self, fr):
        super().__init__(fr)