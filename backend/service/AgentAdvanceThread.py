import threading


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class AgentAdvanceThread(StoppableThread):

    def __init__(self, host, port):
        self.endpoint = "http://" + str(host) + ":" + str(port) + "/iidea/advance"
        super().__init__()

    def run(self):
        while not self.stopped():

            import time
            time.sleep(0.25)

            import urllib.request
            contents = urllib.request.urlopen(self.endpoint).read()