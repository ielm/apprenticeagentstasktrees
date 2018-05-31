from backend.contexts.context import AgendaProcessor, HeuristicException
from backend.contexts.LCTContext import LCTContext
from backend.models.fr import FR
from functools import reduce

import operator


# Finds learned tasks in long-term memory that relate to the input "to do" task, and moves them into working memory.
# To do this, the following must be true:
# 1) The TMR is prefix
# 2) There are matching events in LT memory that have the same concept as the main TMR event, and share at least
#    THEME (by concept).
# For each match found, load the entire of that event (by LCT.from_context ID) into working memory.
class RecallTaskFromLongTermMemoryAgendaProcessor(AgendaProcessor):

    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):

        if not tmr.is_prefix():
            raise HeuristicException()

        def _fillers_to_concepts(graph, fillers):
            from backend.models.frinstance import FRInstance
            fillers = map(lambda filler: filler.value if type(filler) == FRInstance.FRFiller else filler, fillers)
            return set(map(lambda filler: graph[filler].concept, fillers))

        event = tmr.find_main_event()
        themes = _fillers_to_concepts(tmr, event["THEME"])

        results = agent.lt_memory.search(concept=event.concept)
        results = list(filter(lambda result: len(_fillers_to_concepts(agent.lt_memory, result["THEME"]).intersection(themes)) > 0, results))

        if len(results) == 0:
            raise HeuristicException()

        for result in results:
            temp = FR(namespace="TEMP")
            for instance in agent.lt_memory.search(context={LCTContext.FROM_CONTEXT: result.context()[LCTContext.FROM_CONTEXT][0]}):
                temp[instance.name] = instance
            id_map = agent.wo_memory.import_fr(temp)

            agent.wo_memory[id_map[result.name]].context()[self.context.DOING] = True


# Assuming a currently doing task, finds any preconditions for that task and makes them into actions on the agent queue.
# 1) There are events marked as ACT.doing
# 2) Those events have PRECONDITIONs
# For each matching precondition, map it to an action to take (if applicable) and add those actions to the agent queue.
class QueuePreconditionActionsAgendaProcessor(AgendaProcessor):

    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):
        doing = agent.wo_memory.search(context={self.context.DOING: True})

        if len(doing) == 0:
            raise HeuristicException()

        preconditions = list(map(lambda filler: agent.wo_memory[filler.value], reduce(operator.add, map(lambda event: event["PRECONDITION"], doing))))

        if len(preconditions) == 0:
            raise HeuristicException()

        agent.action_queue.extend(set(filter(lambda action: action is not None, map(lambda precondition: self.precondition_to_action(agent, precondition), preconditions))))

    def precondition_to_action(self, agent, precondition):
        if precondition.concept == "POSSESSION-EVENT":
            themes = set(map(lambda theme: agent.wo_memory[theme.value].concept, precondition["THEME"]))

            if len(themes) == 0:
                return None

            actions = list(map(lambda theme: "ROBOT.GET(" + theme + ")", themes))

            return " and ".join(actions)

        return None