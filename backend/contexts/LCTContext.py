from backend.contexts.context import AgentContext, PostHeuristicsProcessor
from backend.ontology import Ontology


# An agent context for (L)earning (C)omplex (T)asks.
class LCTContext(AgentContext):

    def __init__(self, agent):
        super().__init__(agent)

        self.pre_heuristics = [
            self.identify_closing_of_known_task,
        ]

        self.post_heuristics.halt = True
        self.post_heuristics.add_subheuristic(PostHeuristicsProcessor(self.identify_preconditions))
        self.post_heuristics.add_subheuristic(PostHeuristicsProcessor(self.handle_requested_actions))
        self.post_heuristics.add_subheuristic(PostHeuristicsProcessor(self.recognize_sub_events).add_subheuristic(PostHeuristicsProcessor(self.recognize_parts_of_object)))

        agent.st_memory.heuristics.insert(0, LCTContext.resolve_undetermined_themes_of_learning)
        agent.st_memory.heuristics.append(LCTContext.resolve_undetermined_themes_of_learning_in_postfix)
        agent.st_memory.heuristics.append(LCTContext.resolve_learning_events)

    def prepare_static_knowledge(self):
        Ontology.add_filler("FASTEN", "IS-A", "VALUE", "ASSEMBLE")
        Ontology.add_filler("ASSEMBLE", "IS-A", "VALUE", "BUILD")
        Ontology.ontology["BRACKET"] = {
            "IS-A": {
                "VALUE": ["ARTIFACT-PART"]
            },
        }
        Ontology.ontology["DOWEL"] = {
            "IS-A": {
                "VALUE": ["ARTIFACT-PART"]
            },
        }

    # ------ Meta-contextual Properties -------

    LEARNING = "*LCT.learning"          # Marks an event that is being learned; True / False (absent)
    LEARNED = "*LCT.learned"            # Marks an event that has been learned; True / False (absent)
    CURRENT = "*LCT.current"            # Marks an event that is currently being explained; True / False (absent)
    WAITING_ON = "*LCT.waiting_on"      # Marks an event that is waiting on another event to be explained; FR EVENT ID

    # ------ Pre-Heuristics -------

    # Identifies when an utterance is specifying that an already mentioned task or sub-event is now complete.
    # Example: We have assembled a front leg.
    # If the postfix TMR can resolve the main event to the FR, and the resolved event is currently being learned,
    # it is now complete (and all subtasks below it are also completed; any parent task it has is considered current).
    # Finding a match necessarily removes the LEARN_ST_MEMORY and POST_PROCESS agent events as this TMR has been
    # consumed.
    def identify_closing_of_known_task(self, tmr, instructions):

        if tmr.is_postfix():
            resolved = self.agent.st_memory.resolve_tmr(tmr)

            event = tmr.find_main_event()
            hierarchy = self.learning_hierarchy()

            if resolved[event.name] is None:
                return

            target = -1
            for index, le in enumerate(hierarchy):
                if le in resolved[event.name]:
                    if self.agent.st_memory[le].context()[self.LEARNING]:
                        target = index

            for i in range(0, target + 1):
                self.finish_learning(hierarchy[i])

            if target > -1:
                instructions[AgentContext.LEARN_ST_MEMORY] = False
                instructions[AgentContext.POST_PROCESS] = False
                return True

    # ------ Post-Heuristics -------

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

    # Identifies when a TMR is about a currently learning BUILD event.  If so, anything the TMR is building is added
    # as a part of anything that any parent learning event is also building.
    # Example: First, we will build a front leg of [the chair].
    #          I am using the screwdriver to affix [the brackets] on [the dowel] with screws.
    # This is designed to run as a sub-heuristic to detecting sub-events.  To match, the following must happen:
    # 1) The main event is a BUILD event
    # 2) The main event is LCT.learning
    # 3) The main event has one or more "parts" (that is, THEMEs and DESTINATIONs that are OBJECTs)
    # 4) The candidate events are LCT.learning and are LCT.waiting_on the main event
    # 5) The candidate event is a BUILD event
    # 6) The candidate event has exactly one THEME
    # If the above match, add all parts as HAS-OBJECT-AS-PART to the candidate THEME
    def recognize_parts_of_object(self, tmr):

        event = tmr.find_main_event()
        fr_event = self.agent.st_memory.search(attributed_tmr_instance=event)[0]

        parts = list(map(lambda theme: self.agent.st_memory.search(subtree="OBJECT", attributed_tmr_instance=tmr[theme]), event["THEME"]))
        parts += list(map(lambda theme: self.agent.st_memory.search(subtree="OBJECT", attributed_tmr_instance=tmr[theme]), event["DESTINATION"]))
        parts = [item for sublist in parts for item in sublist]

        if len(parts) == 0:
            return

        if not fr_event.context()[self.LEARNING]:
            return

        if not "BUILD" in Ontology.ancestors(fr_event.concept, include_self=True):
            return

        results = self.agent.st_memory.search(context={self.LEARNING: True, self.WAITING_ON: fr_event.name})
        if len(results) == 0:
            return

        success = False
        for result in results:
            if not "BUILD" in Ontology.ancestors(result.concept, include_self=True):
                continue

            if len(result["THEME"]) != 1:
                continue

            theme = self.agent.st_memory[result["THEME"][0].value]

            for part in parts:
                theme.remember("HAS-OBJECT-AS-PART", part.name)
            success = True

        return success

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

    # FR resolution method for identifying that an undetermined ("a chair") object that is the THEME of a
    # resolved EVENT that is currently being learned, is the same THEME as other similar types of THEMEs found
    # in the resolved EVENT, if the TMR is postfix.
    # Example: First, we will build a front leg of the chair.  We have assembled [a front leg].
    # To match, the following must be true:
    #   1) The TMR must be in postfix ("we have")
    #   2) The instance must be an OBJECT
    #   3) The instance must be undetermined ("a chair")
    #   4) The instance must be a THEME-OF an EVENT in the TMR
    #   5) That EVENT must be found (roughly resolved) in the FR by concept match, AND as LCT.learning
    #   6) For each THEME of the matching FR EVENT, any that are the same concept as the instance are resolved matches
    @staticmethod
    def resolve_undetermined_themes_of_learning_in_postfix(fr, instance, resolves, tmr=None):
        if instance.subtree != "OBJECT":
            return

        if tmr is None:
            return

        if tmr.is_prefix():
            return

        dependencies = tmr.syntax.find_dependencies(types=["ART"], governors=instance.token_index)
        articles = list(map(lambda dependency: tmr.syntax.index[str(dependency[2])], dependencies))
        tokens = list(map(lambda article: article["lemma"], articles))

        if "A" not in tokens:
            return

        if "THEME-OF" not in instance:
            return

        theme_ofs = map(lambda theme_of: tmr[theme_of], instance["THEME-OF"])

        matches = set()

        for theme_of in theme_ofs:
            results = fr.search(concept=theme_of.concept, context={LCTContext.LEARNING: True})
            for result in results:
                for theme in result["THEME"]:
                    if fr[theme.value].concept == instance.concept:
                        matches.add(theme.value)

        if len(matches) > 0:
            resolves[instance.name] = matches
            return True

    # FR resolution method for resolving EVENTs against currently learning FR events.
    # Example: First, we will build a front leg of the chair.  We [have assembled] a front leg.
    # To be a match, the following must be true:
    #   1) The instance must be an EVENT
    #   2) A candidate in the FR must be the same concept as the instance
    #   3) A candidate in the FR must be LTC.learning
    #   4) A candidate in the FR must have at least one *resolved* match for each case-role filler specified by
    #      the instance.  (Currently, this includes only AGENT and THEME).  That is, if "AGENT" is defined in the
    #      instance, that filler must a) be resolved, and b) be equal to one of the AGENT fillers in the candidate.
    @staticmethod
    def resolve_learning_events(fr, instance, resolves, tmr=None):
        if instance.subtree != "EVENT":
            return

        if tmr is None:
            return

        matches = set()

        for candidate in fr.search(concept=instance.concept, context={LCTContext.LEARNING: True}):
            case_roles = ["AGENT", "THEME"]

            passed = True
            for case_role in case_roles:
                if case_role in instance:
                    for filler in instance[case_role]:
                        if resolves[filler] is None:
                            passed = False
                            break

                        if len(resolves[filler].intersection(set(map(lambda f: f.value, candidate[case_role])))) == 0:
                            passed = False
                            break

            if passed:
                matches.add(candidate.name)

        if len(matches) > 0:
            resolves[instance.name] = matches
            return True

    # ------ Context Helper Functions -------

    # Helper function for returning the learning hierarchy; starting with LTC.current, and finding each "parent"
    # via the LCT.waiting_on property; the names are returned in that order (element 0 is current).
    def learning_hierarchy(self):
        results = self.agent.st_memory.search(context={LCTContext.LEARNING: True, LCTContext.CURRENT: True})
        if len(results) != 1:
            return

        hierarchy = [results[0].name]

        results = self.agent.st_memory.search(context={LCTContext.LEARNING: True, LCTContext.CURRENT: False, LCTContext.WAITING_ON: hierarchy[-1]})
        while len(results) == 1:
            hierarchy.append(results[0].name)
            results = self.agent.st_memory.search(context={LCTContext.LEARNING: True, LCTContext.CURRENT: False, LCTContext.WAITING_ON: hierarchy[-1]})

        return hierarchy

    # Helper function for marking a single instance that is currently LTC.learning as finished learning.  This means
    # that LCT.learning, LCT.waiting_on, and LCT.current are all removed, while LCT.learned is added.  Further, if
    # this instance has a parent (LCT.waiting_on = instance), that instance is modified to no longer be LCT.waiting_on
    # and is marked as LCT.current if this instance was considered current.
    def finish_learning(self, instance):
        instance = self.agent.st_memory[instance]
        roll_up_current = instance.context()[self.CURRENT]

        for context in [self.LEARNING, self.CURRENT, self.WAITING_ON]:
            if context in instance.context():
                del instance.context()[context]

        instance.context()[self.LEARNED] = True

        for parent in self.agent.st_memory.search(context={self.WAITING_ON: instance.name}):
            if roll_up_current:
                parent.context()[self.CURRENT] = True
            if self.WAITING_ON in parent.context():
                del parent.context()[self.WAITING_ON]