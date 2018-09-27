

class AgentLogger(object):
    """
    Agent Logger
    """

    INDENT = "   "

    def __init__(self):
        self._log = False
        self._paused_status = None
        self._indent = 0

    def enable(self):
        self._log = True

    def disable(self):
        self._log = False

    def pause(self):
        self._paused_status = self._log
        self.disable()

    def unpause(self):
        self._log = self._paused_status
        self._paused_status = None

    def indent(self):
        self._indent += 1

    def unindent(self):
        self._indent -= 1

    def log(self, message):
        if not self._log:
            return

        out = ""
        for i in range(0, self._indent):
            out += AgentLogger.INDENT

        out += message
        self._out(out)

    def _out(self, message):
        print(message)


class CachedAgentLogger(AgentLogger):

    def __init__(self):
        super().__init__()
        self._cache = []

    def _out(self, message):
        self._cache.append(message)

