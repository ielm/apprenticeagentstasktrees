from backend.contexts.context import AgentContext


# An agent context for (L)earning (C)omplex (T)asks.
class LCTContext(AgentContext):

    def __init__(self, agent):
        super().__init__(agent)

        self.heuristics = [
            self.recognize_sub_events,
        ]

    # ------ Meta-contextual Properties -------

    LEARNING = "*LCT.learning"          # Marks an event that is being learned; True / False (absent)
    CURRENT = "*LCT.current"            # Marks an event that is currently being explained; True / False (absent)
    WAITING_ON = "*LCT.waiting_on"      # Marks an event that is waiting on another event to be explained; FR EVENT ID

    # ------ Heuristics -------

    def recognize_sub_events(self, tmr):

        if tmr.is_prefix():
            event = tmr.find_main_event()
            fr_event = self.agent.st_memory.search(attributed_tmr_instance=event)[0]

            fr_currently_learning_events = self.agent.st_memory.search(context={self.LEARNING: True})
            for fr_current_event in fr_currently_learning_events:
                fr_current_event.context()[self.CURRENT] = False
                fr_current_event.context()[self.WAITING_ON] = fr_event.name
                fr_current_event.remember("HAS-EVENT-AS-PART", fr_event.name)

            fr_event.context()[self.LEARNING] = True
            fr_event.context()[self.CURRENT] = True
