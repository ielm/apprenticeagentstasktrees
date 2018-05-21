from backend.contexts.context import AgentContext
from backend.ontology import Ontology


# An agent context for (L)earning (C)omplex (T)asks.
class LCTContext(AgentContext):

    def __init__(self, agent):
        super().__init__(agent)

        self.heuristics = [
            self.identify_preconditions,
            self.handle_requested_actions,
            self.recognize_sub_events,
        ]

        agent.st_memory.heuristics.insert(0, LCTContext.resolve_undetermined_themes_of_learning)

    def prepare_static_knowledge(self):
        Ontology.add_filler("FASTEN", "IS-A", "VALUE", "ASSEMBLE")
        Ontology.add_filler("ASSEMBLE", "IS-A", "VALUE", "BUILD")

    # ------ Meta-contextual Properties -------

    LEARNING = "*LCT.learning"          # Marks an event that is being learned; True / False (absent)
    CURRENT = "*LCT.current"            # Marks an event that is currently being explained; True / False (absent)
    WAITING_ON = "*LCT.waiting_on"      # Marks an event that is waiting on another event to be explained; FR EVENT ID

    # ------ Heuristics -------

    # Identifies when an utterance is specifying a precondition (and not some specific action to be taken).
    # Example: I need a screwdriver to assemble a chair.
    # If the main event of the TMR has a PURPOSE, find any LCT.learning frames with matching important
    # case-roles to the PURPOSE, and add the main event as a PRECONDITION to those results.
    def identify_preconditions(self, tmr):

        if tmr.is_prefix():
            event = tmr.find_main_event()
            fr_event = self.agent.st_memory.search(attributed_tmr_instance=event)[0]

            found = False
            for p in fr_event["PURPOSE"]:
                purpose = self.agent.st_memory[p.value]

                case_roles_to_match = ["AGENT", "THEME"]
                filler_query = {}
                for cr in case_roles_to_match:
                    if cr in purpose:
                        filler_query[cr] = purpose[cr][0].value

                results = self.agent.st_memory.search(context={self.LEARNING: True}, has_fillers=filler_query)
                for result in results:
                    result.remember("PRECONDITION", fr_event.name)

                if len(results) > 0:
                    found = True

            if found:
                return True

    # Identifies when an utterance is requesting a simple action (the LCT.current does not have to move).
    # Example: Get a screwdriver.
    # If the main event of the TMR is a REQUEST-ACTION, and the ROBOT is the BENEFICIARY, then add the event
    # to the HAS-EVENT-AS-PART slot of the LCT.learning / LCT.current event (but do not change LCT.current).
    def handle_requested_actions(self, tmr):

        if tmr.is_prefix():
            event = tmr.find_main_event()
            fr_event = self.agent.st_memory.search(attributed_tmr_instance=event)[0]

            if event.concept == "REQUEST-ACTION" and "ROBOT" in event["BENEFICIARY"]:
                fr_currently_learning_events = self.agent.st_memory.search(context={self.LEARNING: True, self.CURRENT: True})
                for fr_current_event in fr_currently_learning_events:
                    fr_current_event.remember("HAS-EVENT-AS-PART", fr_event.name)

                return True

    # Identifies when an utterance is exposing a new complex sub-event (this will result in LCT.current changing).
    # Example: First, we will build a front leg of the chair.
    # This is considered the default (fallback) heuristic for PREFIX TMRs.  That is, if all other PREFIX heuristics
    # fail to match, this action is taken:
    #   Find the LCT.learning / LCT.current fr event, and add this main event to the HAS-EVENT-AS-PART slot.  Then,
    #   set the LCT.current to False, the LCT.waiting_on to this main event, assign LCT.current and LCT.learning to
    #   this main event.
    def recognize_sub_events(self, tmr):

        if tmr.is_prefix():
            event = tmr.find_main_event()
            fr_event = self.agent.st_memory.search(attributed_tmr_instance=event)[0]

            fr_currently_learning_events = self.agent.st_memory.search(context={self.LEARNING: True, self.CURRENT: True})
            for fr_current_event in fr_currently_learning_events:
                fr_current_event.context()[self.CURRENT] = False
                fr_current_event.context()[self.WAITING_ON] = fr_event.name
                fr_current_event.remember("HAS-EVENT-AS-PART", fr_event.name)

            fr_event.context()[self.LEARNING] = True
            fr_event.context()[self.CURRENT] = True

            return True

    # ------ FR Resolution Heuristics -------

    # FR resolution method used to connect an instance that is undetermined ("a chair" rather than "the chair") to an
    # existing FR instance by looking for instances that are the "themes of learning" (in other words, what is currently
    # being learned).
    # Example: We will build a chair.  I need a screwdriver to assemble [a chair].
    #   The 2nd instance of "a chair" would typically not be connected to the first, due to the lack of a determiner.
    #   However, as the first usage of "a chair" kicked off a theme of learning (that is still active), we are more
    #   flexible with resolution.
    # To do this:
    #   1) The instance to resolve must be an OBJECT
    #   2) The instance to resolve must be undetermined ("a chair")
    #   3) The instance must be the THEME of an EVENT that also has a PURPOSE, which must be another EVENT
    #   4) If so, then any corresponding concept match in the FR is a valid resolution
    #      Note, this last match is a little broad, but is ok in that this resolution heuristic operates in short-term
    #      memory only.
    @staticmethod
    def resolve_undetermined_themes_of_learning(fr, instance, resolves, tmr=None):
        if instance.subtree != "OBJECT":
            return

        if tmr is None:
            return

        dependencies = tmr.syntax.find_dependencies(types=["ART"], governors=instance.token_index)
        articles = list(map(lambda dependency: tmr.syntax.index[str(dependency[2])], dependencies))
        tokens = list(map(lambda article: article["lemma"], articles))

        if "A" not in tokens:
            return

        if "THEME-OF" not in instance:
            return

        theme_ofs = map(lambda theme_of: tmr[theme_of], instance["THEME-OF"])

        for theme_of in theme_ofs:
            if "PURPOSE-OF" in theme_of:
                purpose_ofs = map(lambda purpose_of: tmr[purpose_of], theme_of["PURPOSE-OF"])
                purpose_ofs = filter(lambda purpose_of: purpose_of.subtree == "EVENT", purpose_ofs)
                if len(list(purpose_ofs)) > 0:
                    results = fr.search(concept=instance.concept)
                    resolves[instance.name] = set(map(lambda result: result.name, results))
                    return True