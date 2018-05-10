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

    def handle_requested_actions(self, tmr):

        if tmr.is_prefix():
            event = tmr.find_main_event()
            fr_event = self.agent.st_memory.search(attributed_tmr_instance=event)[0]

            if event.concept == "REQUEST-ACTION" and "ROBOT" in event["BENEFICIARY"]:
                fr_currently_learning_events = self.agent.st_memory.search(context={self.LEARNING: True, self.CURRENT: True})
                for fr_current_event in fr_currently_learning_events:
                    fr_current_event.remember("HAS-EVENT-AS-PART", fr_event.name)

                return True

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