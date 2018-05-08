from backend.models.fr import FR
from backend.models.tmr import TMR


class Agent(object):

    def __init__(self):
        self.st_memory = FR()   # Short-term memory
        self.lt_memory = FR()   # Long-term memory

        self.input_memory = []

    def input(self, input):
        tmr = TMR(input)
        self.input_memory.append(tmr)
        self.st_memory.learn_tmr(tmr)

        self.learn_with_context(tmr)

    def learn_with_context(self, tmr):
        # If the main event is a prefix
            # Context.learning = True
            # Context.current = True
            # Find any other Context.learning:
                # set Context.current = False
                # Context.waiting_on = this
                # has-event-as-part = this

        if tmr.is_prefix():
            event = tmr.find_main_event()
            fr_event = self.st_memory.search(attributed_tmr_instance=event)[0]

            fr_currently_learning_events = self.st_memory.search(context={"learning": True})
            for fr_current_event in fr_currently_learning_events:
                fr_current_event.set_context("current", False)
                fr_current_event.set_context("waiting_on", fr_event.name)
                fr_current_event.remember("HAS-EVENT-AS-PART", fr_event.name)

            fr_event.set_context("learning", True)
            fr_event.set_context("current", True)