from backend.contexts.context import HeuristicException, UnderstandingProcessor
from backend.contexts.LCTContext import LCTContext
from backend.models.fr import FR
from backend.models.graph import Frame, Identifier
from functools import reduce

import operator


# Finds learned tasks in long-term memory that relate to the input "to do" task, and moves them into working memory.
# To do this, the following must be true:
# 1) The TMR is prefix
# 2) There are matching events in LT memory that have the same concept as the main TMR event, and share at least
#    THEME (by concept).
# For each match found, load the entire of that event (by LCT.from_context ID) into working memory.
class RecallTaskFromLongTermMemoryUnderstandingProcessor(UnderstandingProcessor):

    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):

        if not tmr.is_prefix():
            raise HeuristicException()

        def _fillers_to_concepts(graph, fillers):
            return set(map(lambda filler: filler.resolve().concept(), fillers))

        event = tmr.find_main_event()
        themes = _fillers_to_concepts(tmr, event["THEME"])

        results = agent.lt_memory.search(Frame.q(agent).isa(event.concept()))
        results = list(filter(lambda result: len(_fillers_to_concepts(agent.lt_memory, result["THEME"]).intersection(themes)) > 0, results))

        if len(results) == 0:
            raise HeuristicException()

        for result in results:
            id_map = {}
            temp = FR("TEMP", agent.ontology)
            for instance in agent.lt_memory.search(Frame.q(agent).f(LCTContext.FROM_CONTEXT, result[LCTContext.FROM_CONTEXT][0])):
                id_map[instance._identifier.render()] = instance._identifier.render(graph=False)
                id = Identifier(None, instance._identifier.name, instance=instance._identifier.instance)
                temp[id] = instance

            for instance in temp:
                for slot in temp[instance]:
                    for filler in temp[instance][slot]:
                        if isinstance(filler._value, Identifier) and filler._value.render() in id_map:
                            filler._value = id_map[filler._value.render()]

            id_map = agent.wo_memory.import_fr(temp)

            agent.wo_memory[id_map[result._identifier.render()]][self.context.DOING] = True


# Assuming a currently doing task, finds any preconditions for that task and makes them into actions on the agent queue.
# 1) There are events marked as ACT.doing
# 2) Those events have PRECONDITIONs
# For each matching precondition, map it to an action to take (if applicable) and add those actions to the agent queue.
class QueuePreconditionActionsUnderstandingProcessor(UnderstandingProcessor):

    def __init__(self, context):
        super().__init__()
        self.context = context

    def _logic(self, agent, tmr):
        doing = agent.wo_memory.search(Frame.q(agent).f(self.context.DOING, True))

        if len(doing) == 0:
            raise HeuristicException()

        preconditions = list(map(lambda filler: filler.resolve(), reduce(operator.add, map(lambda event: event["PRECONDITION"], doing))))

        if len(preconditions) == 0:
            raise HeuristicException()

        agent.action_queue.extend(set(filter(lambda action: action is not None, map(lambda precondition: self.precondition_to_action(agent, precondition), preconditions))))

    def precondition_to_action(self, agent, precondition):
        if precondition ^ agent.ontology["POSSESSION-EVENT"]:
            themes = set(map(lambda theme: theme.resolve().concept(), precondition["THEME"]))

            if len(themes) == 0:
                return None

            actions = list(map(lambda theme: "ROBOT.GET(" + theme + ")", themes))

            return " and ".join(actions)

        return None