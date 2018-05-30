from backend.contexts.context import AgentContext, AgendaProcessor, FRResolutionAgendaProcessor, HeuristicException, RootAgendaProcessor
from backend.heuristics.fr_heuristics import FRHeuristics
from backend.ontology import Ontology
from backend.utils import FRUtils


# An agent context for (L)earning (C)omplex (T)asks.
class LCTContext(AgentContext):

    def __init__(self, agent):
        super().__init__(agent)

        agent.wo_memory.heuristics.insert(0, LCTContext.resolve_undetermined_themes_of_learning)
        agent.wo_memory.heuristics.append(LCTContext.resolve_undetermined_themes_of_learning_in_postfix)
        agent.wo_memory.heuristics.append(LCTContext.resolve_learning_events)

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

    def default_agenda(self):

        agenda = RootAgendaProcessor()

        agenda.add_subprocess(LCTContext.IdentifyClosingOfKnownTaskAgendaProcessor(self).add_subprocess(LCTContext.IdentifyCompletedTaskAgendaProcessor()))
        agenda.add_subprocess(LCTContext.IdentifyPreconditionSatisfyingActionsAgendaProcessor())
        agenda.add_subprocess(FRResolutionAgendaProcessor())
        agenda.add_subprocess(LCTContext.IdentifyPreconditionsAgendaProcessor())
        agenda.add_subprocess(LCTContext.HandleRequestedActionsAgendaProcessor())
        agenda.add_subprocess(LCTContext.HandleCurrentActionAgendaProcessor())
        agenda.add_subprocess(LCTContext.RecognizeSubEventsAgendaProcessor().add_subprocess(LCTContext.RecognizePartsOfObjectAgendaProcessor()))
        agenda.add_subprocess(LCTContext.IdentifyClosingOfUnknownTaskAgendaProcessor(self))

        return agenda

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
    class IdentifyClosingOfKnownTaskAgendaProcessor(AgendaProcessor):
        def __init__(self, context):
            super().__init__()
            self.context = context

        def _logic(self, agent, tmr):
            if tmr.is_postfix():

                agent.wo_memory.logger().pause()
                resolved = agent.wo_memory.resolve_tmr(tmr)
                agent.wo_memory.logger().unpause()

                event = tmr.find_main_event()
                hierarchy = self.context.learning_hierarchy()

                if resolved[event.name] is None:
                    raise HeuristicException()

                target = -1
                for index, le in enumerate(hierarchy):
                    if le in resolved[event.name]:
                        if agent.wo_memory[le].context()[LCTContext.LEARNING]:
                            target = index

                for i in range(0, target + 1):
                    self.context.finish_learning(hierarchy[i])

                if target > -1:
                    self.halt_siblings()
                    return

            raise HeuristicException()

    # Identifies when an utterance signals that the currently learning task (overall) is complete.
    # Example: We finished assembling the chair.
    # This holds true if:
    # 1) The TMR is postfix
    # 2) There is at least one LCT.learned event in working memory
    # 3) There are no LCT.learning events in working memory
    # If this heuristic matches, it will import working memory into long term memory, using the FR import heuristics
    # defined in this context, and then will clear working memory.
    class IdentifyCompletedTaskAgendaProcessor(AgendaProcessor):
        def _logic(self, agent, tmr):
            if not tmr.is_postfix():
                raise HeuristicException()

            if len(agent.wo_memory.search(context={LCTContext.LEARNED: True})) == 0:
                raise HeuristicException()

            if len(agent.wo_memory.search(context={LCTContext.LEARNING: True})) > 0:
                raise HeuristicException()

            agent.lt_memory.import_fr(agent.wo_memory, import_heuristics=[LCTContext.do_not_import_request_actions], resolve_heuristics=[FRHeuristics.resolve_human_and_robot_as_singletons, FRHeuristics.resolve_sets_with_identical_members])
            agent.wo_memory.clear()

    # Identifies when an action is simply satisfying a precondition; if so, it is not "learned", as the precondition
    # is already known.
    # Example: I need a screwdriver to assemble a chair.  [Get a screwdriver.]
    # To be a match, the following must be true:
    # 1) The TMR is current (not pre- or postfix).
    # 2) There must be previous input in the context (this cannot be the first TMR).
    # 3) The main event must be a REQUEST-ACTION with BENEFICIARY = ROBOT.
    # 4) The immediately previous TMR (last input) must have been current (not pre- or postfix).
    # 5) The previous TMR's main event must have a PURPOSE (this is currently the identifier of a precondition utterance).
    # 6) The theme of this TMR's REQUEST-ACTION.THEME must match the THEME of the previous TMR's main event (concept match only).
    # If the above hold, the input is skipped and all other heuristics are disabled.
    class IdentifyPreconditionSatisfyingActionsAgendaProcessor(AgendaProcessor):
        def _logic(self, agent, tmr):
            if tmr.is_prefix() or tmr.is_postfix():
                raise HeuristicException()

            if len(agent.input_memory) < 2:
                raise HeuristicException()

            event = tmr.find_main_event()
            if event.concept != "REQUEST-ACTION" or "ROBOT" not in event["BENEFICIARY"]:
                raise HeuristicException()

            previous_tmr = agent.input_memory[-2]
            if previous_tmr.is_prefix() or previous_tmr.is_postfix():
                raise HeuristicException()

            previous_event = previous_tmr.find_main_event()
            if "PURPOSE" not in previous_event:
                raise HeuristicException()

            if len(event["THEME"]) > 1:
                raise HeuristicException()

            event = tmr[event["THEME"][0]]

            themes = event["THEME"]
            themes = list(map(lambda theme: tmr[theme].concept, themes))

            previous_themes = previous_event["THEME"]
            previous_themes = list(map(lambda theme: previous_tmr[theme].concept, previous_themes))

            if len(set(themes).intersection(set(previous_themes))) > 0:
                self.reassign_siblings([FRResolutionAgendaProcessor()])
                return

            raise HeuristicException()

    # ------ Post-Heuristics -------

    # Identifies when an utterance is specifying a precondition (and not some specific action to be taken).
    # Example: I need a screwdriver to assemble a chair.
    # If the main event of the TMR has a PURPOSE, find any LCT.learning frames with matching important
    # case-roles to the PURPOSE, and add the main event as a PRECONDITION to those results.
    class IdentifyPreconditionsAgendaProcessor(AgendaProcessor):
        def _logic(self, agent, tmr):
            if not tmr.is_prefix() and not tmr.is_postfix():
                event = tmr.find_main_event()
                fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]

                found = False
                for p in fr_event["PURPOSE"]:
                    purpose = agent.wo_memory[p.value]

                    case_roles_to_match = ["AGENT", "THEME"]
                    filler_query = {}
                    for cr in case_roles_to_match:
                        if cr in purpose:
                            filler_query[cr] = purpose[cr][0].value

                    results = agent.wo_memory.search(context={LCTContext.LEARNING: True}, has_fillers=filler_query)
                    for result in results:
                        result.remember("PRECONDITION", fr_event.name)

                    if len(results) > 0:
                        found = True

                if found:
                    self.halt_siblings()
                    return

            raise HeuristicException()

    # Identifies when an utterance is requesting a simple action (the LCT.current does not have to move).
    # Example: Get a screwdriver.
    # If the main event of the TMR is a REQUEST-ACTION, and the ROBOT is the BENEFICIARY, then add the event's THEMEs
    # to the HAS-EVENT-AS-PART slot of the LCT.learning / LCT.current event (but do not change LCT.current).
    class HandleRequestedActionsAgendaProcessor(AgendaProcessor):
        def _logic(self, agent, tmr):
            if tmr.is_prefix() or tmr.is_postfix():
                raise HeuristicException()

            event = tmr.find_main_event()
            fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]
            fr_themes = fr_event["THEME"]

            if event.concept == "REQUEST-ACTION" and "ROBOT" in event["BENEFICIARY"]:
                fr_currently_learning_events = agent.wo_memory.search(
                    context={LCTContext.LEARNING: True, LCTContext.CURRENT: True})
                for fr_current_event in fr_currently_learning_events:
                    for theme in fr_themes:
                        fr_current_event.remember("HAS-EVENT-AS-PART", theme.value)

                self.halt_siblings()
                return

            raise HeuristicException()

    # Identifies actions that are happening "now" (not pre- or postfix), and adds them as children of the current
    # learning context.  This is similar to HandleRequestedActionsAgendaProcessor, without the mapping to the
    # the THEME of the main event (the main event itself is assumed to be the learned event).
    # Example: I am using the screwdriver to affix the brackets on the dowel with screws.
    class HandleCurrentActionAgendaProcessor(AgendaProcessor):
        def _logic(self, agent, tmr):
            if not tmr.is_prefix() and not tmr.is_postfix():
                event = tmr.find_main_event()
                fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]

                fr_currently_learning_events = agent.wo_memory.search(
                    context={LCTContext.LEARNING: True, LCTContext.CURRENT: True})
                for fr_current_event in fr_currently_learning_events:
                    fr_current_event.remember("HAS-EVENT-AS-PART", fr_event.name)

                self.halt_siblings()
                return

            raise HeuristicException()

    # Identifies when an utterance is exposing a new complex sub-event (this will result in LCT.current changing).
    # Example: First, we will build a front leg of the chair.
    # This is considered the default (fallback) heuristic for PREFIX TMRs.  That is, if all other PREFIX heuristics
    # fail to match, this action is taken:
    #   Find the LCT.learning / LCT.current fr event, and add this main event to the HAS-EVENT-AS-PART slot.  Then,
    #   set the LCT.current to False, the LCT.waiting_on to this main event, assign LCT.current and LCT.learning to
    #   this main event.
    class RecognizeSubEventsAgendaProcessor(AgendaProcessor):
        def _logic(self, agent, tmr):
            if tmr.is_prefix():
                event = tmr.find_main_event()
                fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]

                fr_currently_learning_events = agent.wo_memory.search(
                    context={LCTContext.LEARNING: True, LCTContext.CURRENT: True})
                for fr_current_event in fr_currently_learning_events:
                    fr_current_event.context()[LCTContext.CURRENT] = False
                    fr_current_event.context()[LCTContext.WAITING_ON] = fr_event.name
                    fr_current_event.remember("HAS-EVENT-AS-PART", fr_event.name)

                fr_event.context()[LCTContext.LEARNING] = True
                fr_event.context()[LCTContext.CURRENT] = True

                self.halt_siblings()
                return

            raise HeuristicException()

    # Identifies when an utterance is specifying that some previous tasks were a part of an undisclosed task that is
    # now complete.
    # Example: We have assembled a front leg.
    #          (Assuming that "First, we will build a front leg of the chair." was not uttered).
    # To match, the following must be true:
    # 1) The TMR is postfix.
    # 2) There is an existing event being learned (at least an LCT.current)
    # 3) There is no event being learned that is the same concept as the main event, and shares the same THEME
    #    (concept match only).
    # If the criteria match, the main event will be added as a child of the LCT.current; any children of the LCT.current
    # that are not complex events (do not have HAS-EVENT-AS-PART) will be moved to be children of the main event.
    class IdentifyClosingOfUnknownTaskAgendaProcessor(AgendaProcessor):
        def __init__(self, context):
            super().__init__()
            self.context = context

        def _logic(self, agent, tmr):
            if not tmr.is_postfix():
                raise HeuristicException()

            event = tmr.find_main_event()
            fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]

            hierarchy = self.context.learning_hierarchy()

            if len(hierarchy) == 0:
                raise HeuristicException()

            for learning in hierarchy:
                learning = agent.wo_memory[learning]
                if learning.concept != fr_event.concept:
                    continue
                if not FRUtils.comparator(agent.wo_memory, fr_event, learning, "THEME", compare_concepts=True):
                    continue
                raise HeuristicException()

            current = agent.wo_memory[hierarchy[0]]

            children = list(map(lambda child: agent.wo_memory[child.value], current["HAS-EVENT-AS-PART"]))
            children = list(filter(lambda child: "HAS-EVENT-AS-PART" not in child, children))

            current.context()[LCTContext.CURRENT] = False
            current.context()[LCTContext.WAITING_ON] = fr_event.name
            current.remember("HAS-EVENT-AS-PART", fr_event.name)

            fr_event.context()[LCTContext.LEARNING] = True
            fr_event.context()[LCTContext.CURRENT] = True

            for child in children:
                current.forget("HAS-EVENT-AS-PART", child.name)
                fr_event.remember("HAS-EVENT-AS-PART", child.name)

            self.context.finish_learning(fr_event.name)

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
    class RecognizePartsOfObjectAgendaProcessor(AgendaProcessor):
        def _logic(self, agent, tmr):
            event = tmr.find_main_event()
            fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]

            parts = list(
                map(lambda theme: agent.wo_memory.search(subtree="OBJECT", attributed_tmr_instance=tmr[theme]),
                    event["THEME"]))
            parts += list(
                map(lambda theme: agent.wo_memory.search(subtree="OBJECT", attributed_tmr_instance=tmr[theme]),
                    event["DESTINATION"]))
            parts = [item for sublist in parts for item in sublist]

            if len(parts) == 0:
                raise HeuristicException()

            if LCTContext.LEARNING not in fr_event.context() or not fr_event.context()[LCTContext.LEARNING]:
                raise HeuristicException()

            if not "BUILD" in Ontology.ancestors(fr_event.concept, include_self=True):
                raise HeuristicException()

            results = agent.wo_memory.search(context={LCTContext.LEARNING: True, LCTContext.WAITING_ON: fr_event.name})
            if len(results) == 0:
                raise HeuristicException()

            success = False
            for result in results:
                if not "BUILD" in Ontology.ancestors(result.concept, include_self=True):
                    continue

                if len(result["THEME"]) != 1:
                    continue

                theme = agent.wo_memory[result["THEME"][0].value]

                for part in parts:
                    theme.remember("HAS-OBJECT-AS-PART", part.name)
                success = True

            if success:
                return

            raise HeuristicException()

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

    # ------ FR Import Heuristics -------

    # An import heuristic that filters out request action frames; these are not needed to be moved to long term memory.
    @staticmethod
    def do_not_import_request_actions(fr, status):
        for instance in fr:
            if fr[instance].concept == "REQUEST-ACTION":
                status[instance] = False

    # ------ Context Helper Functions -------

    # Helper function for returning the learning hierarchy; starting with LTC.current, and finding each "parent"
    # via the LCT.waiting_on property; the names are returned in that order (element 0 is current).
    def learning_hierarchy(self):
        results = self.agent.wo_memory.search(context={LCTContext.LEARNING: True, LCTContext.CURRENT: True})
        if len(results) != 1:
            return

        hierarchy = [results[0].name]

        results = self.agent.wo_memory.search(context={LCTContext.LEARNING: True, LCTContext.CURRENT: False, LCTContext.WAITING_ON: hierarchy[-1]})
        while len(results) == 1:
            hierarchy.append(results[0].name)
            results = self.agent.wo_memory.search(context={LCTContext.LEARNING: True, LCTContext.CURRENT: False, LCTContext.WAITING_ON: hierarchy[-1]})

        return hierarchy

    # Helper function for marking a single instance that is currently LTC.learning as finished learning.  This means
    # that LCT.learning, LCT.waiting_on, and LCT.current are all removed, while LCT.learned is added.  Further, if
    # this instance has a parent (LCT.waiting_on = instance), that instance is modified to no longer be LCT.waiting_on
    # and is marked as LCT.current if this instance was considered current.
    def finish_learning(self, instance):
        instance = self.agent.wo_memory[instance]
        roll_up_current = instance.context()[self.CURRENT]

        for context in [self.LEARNING, self.CURRENT, self.WAITING_ON]:
            if context in instance.context():
                del instance.context()[context]

        instance.context()[self.LEARNED] = True

        for parent in self.agent.wo_memory.search(context={self.WAITING_ON: instance.name}):
            if roll_up_current:
                parent.context()[self.CURRENT] = True
            if self.WAITING_ON in parent.context():
                del parent.context()[self.WAITING_ON]