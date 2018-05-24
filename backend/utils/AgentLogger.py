

class AgentLogger(object):

    INDENT = "   "

    def __init__(self):
        self._log = False
        self._indent = 0

    def enable(self):
        self._log = True

    def disable(self):
        self._log = False

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

