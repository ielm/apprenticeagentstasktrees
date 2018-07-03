from backend.contexts.context import AgendaProcessor, HeuristicException
from backend.models.query import Query
from backend.utils import FRUtils


# ------ Post-Heuristics -------

# Identifies when an utterance is specifying a precondition (and not some specific action to be taken).
# Example: I need a screwdriver to assemble a chair.
# If the main event of the TMR has a PURPOSE, find any LCT.learning frames with matching important
# case-roles to the PURPOSE, and add the main event as a PRECONDITION to those results.
class IdentifyPreconditionsAgendaProcessor(AgendaProcessor):

    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):
        if not tmr.is_prefix() and not tmr.is_postfix():
            event = tmr.find_main_event()
            fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]

            found = False
            for p in fr_event["PURPOSE"]:
                purpose = p.resolve()

                case_roles_to_match = ["AGENT", "THEME"]
                filler_query = {}
                for cr in case_roles_to_match:
                    if cr in purpose:
                        filler_query[cr] = purpose[cr][0].resolve()

                results = agent.wo_memory.search(query=Query.parsef(agent.network, "WHERE {LEARNING} = True", LEARNING=self.context.LEARNING), has_fillers=filler_query)
                for result in results:
                    result["PRECONDITION"] += fr_event

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
    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):
        if tmr.is_prefix() or tmr.is_postfix():
            raise HeuristicException()

        event = tmr.find_main_event()
        fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]
        fr_themes = fr_event["THEME"]

        if event ^ agent.ontology["REQUEST-ACTION"] and "ROBOT" in event["BENEFICIARY"]:
            fr_currently_learning_events = agent.wo_memory.search(
                query=Query.parsef(agent.network, "WHERE ({LEARNING} = True and {CURRENT} = True)", LEARNING=self.context.LEARNING, CURRENT=self.context.CURRENT))
            for fr_current_event in fr_currently_learning_events:
                for theme in fr_themes:
                    fr_current_event["HAS-EVENT-AS-PART"] += theme

            self.halt_siblings()
            return

        raise HeuristicException()


# Identifies actions that are happening "now" (not pre- or postfix), and adds them as children of the current
# learning context.  This is similar to HandleRequestedActionsAgendaProcessor, without the mapping to the
# the THEME of the main event (the main event itself is assumed to be the learned event).
# Example: I am using the screwdriver to affix the brackets on the dowel with screws.
class HandleCurrentActionAgendaProcessor(AgendaProcessor):

    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):
        if not tmr.is_prefix() and not tmr.is_postfix():
            event = tmr.find_main_event()
            fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]

            fr_currently_learning_events = agent.wo_memory.search(
                query=Query.parsef(agent.network, "WHERE ({LEARNING} = True and {CURRENT} = True)", LEARNING=self.context.LEARNING, CURRENT=self.context.CURRENT))
            for fr_current_event in fr_currently_learning_events:
                fr_current_event["HAS-EVENT-AS-PART"] += fr_event

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

    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):
        if tmr.is_prefix():
            event = tmr.find_main_event()
            fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]

            fr_currently_learning_events = agent.wo_memory.search(
                query=Query.parse(agent.network, "WHERE (" + self.context.LEARNING + " = True and " + self.context.CURRENT + " = True)"))
            for fr_current_event in fr_currently_learning_events:
                fr_current_event[self.context.CURRENT] = False
                fr_current_event[self.context.WAITING_ON] = fr_event.name()
                fr_current_event["HAS-EVENT-AS-PART"] += fr_event

            fr_event[self.context.LEARNING] = True
            fr_event[self.context.CURRENT] = True

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

        children = list(map(lambda child: child.resolve(), current["HAS-EVENT-AS-PART"]))
        children = list(filter(lambda child: "HAS-EVENT-AS-PART" not in child, children))

        current.context()[self.context.CURRENT] = False
        current.context()[self.context.WAITING_ON] = fr_event.name()
        current["HAS-EVENT-AS-PART"] += fr_event

        fr_event.context()[self.context.LEARNING] = True
        fr_event.context()[self.context.CURRENT] = True

        for child in children:
            current["HAS-EVENT-AS-PART"] -= child
            fr_event["HAS-EVENT-AS-PART"] += child

        self.context.finish_learning(fr_event.name())


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

    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):
        event = tmr.find_main_event()
        fr_event = agent.wo_memory.search(attributed_tmr_instance=event)[0]

        parts = list(
            map(lambda theme: agent.wo_memory.search(subtree=agent.ontology["OBJECT"], attributed_tmr_instance=theme.resolve()),
                event["THEME"]))
        parts += list(
            map(lambda theme: agent.wo_memory.search(subtree=agent.ontology["OBJECT"], attributed_tmr_instance=theme.resolve()),
                event["DESTINATION"]))
        parts = [item for sublist in parts for item in sublist]

        if len(parts) == 0:
            raise HeuristicException()

        if self.context.LEARNING not in fr_event or not fr_event[self.context.LEARNING]:
            raise HeuristicException()

        if not fr_event ^ agent.ontology["BUILD"]:
            raise HeuristicException()

        results = agent.wo_memory.search(query=Query.parsef(agent.network, "WHERE ({LEARNING} = True and {WAITING_ON} = {EVENT})", LEARNING=self.context.LEARNING, WAITING_ON=self.context.WAITING_ON, EVENT=fr_event.name()))
        if len(results) == 0:
            raise HeuristicException()

        success = False
        for result in results:
            if not result ^ agent.ontology["BUILD"]:
                continue

            if len(result["THEME"]) != 1:
                continue

            theme = result["THEME"][0].resolve()

            for part in parts:
                theme["HAS-OBJECT-AS-PART"] += part
            success = True

        if success:
            return

        raise HeuristicException()