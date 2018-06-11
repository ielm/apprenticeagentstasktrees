from backend.contexts.context import AgendaProcessor, HeuristicException, FRResolutionAgendaProcessor
from backend.heuristics.fr_heuristics import FRResolveHumanAndRobotAsSingletonsHeuristic, FRResolveSetsWithIdenticalMembersHeuristic
from backend.heuristics.lctcontex.lct_fr_import_heuristics import FRImportDoNotImportRequestActions

from uuid import uuid4

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
                    if agent.wo_memory[le].context()[self.context.LEARNING]:
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

    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):
        if not tmr.is_postfix():
            raise HeuristicException()

        if len(agent.wo_memory.search(context={self.context.LEARNED: True})) == 0:
            raise HeuristicException()

        if len(agent.wo_memory.search(context={self.context.LEARNING: True})) > 0:
            raise HeuristicException()

        agent.lt_memory.import_fr(agent.wo_memory,
                                  import_heuristics=[FRImportDoNotImportRequestActions],
                                  resolve_heuristics=[FRResolveHumanAndRobotAsSingletonsHeuristic, FRResolveSetsWithIdenticalMembersHeuristic],
                                  update_context={self.context.FROM_CONTEXT: [uuid4()]})
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

    def __init__(self, context):
        super().__init__()
        self.context = context

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