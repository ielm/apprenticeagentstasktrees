from backend.contexts.context import AgentContext, RootAgendaProcessor

from backend.heuristics.lctcontex.lct_fr_resolution_heuristics import *
from backend.heuristics.lctcontex.lct_post_heuristics import *
from backend.heuristics.lctcontex.lct_pre_heuristics import *


# An agent context for (L)earning (C)omplex (T)asks.
class LCTContext(AgentContext):

    def __init__(self, agent):
        super().__init__(agent)

        agent.wo_memory.heuristics.insert(0, FRResolveUndeterminedThemesOfLearning)
        agent.wo_memory.heuristics.append(FRResolveUnderterminedThemesOfLearningInPostfix)
        agent.wo_memory.heuristics.append(FRResolveLearningEvents)

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

        agenda.add_subprocess(IdentifyClosingOfKnownTaskAgendaProcessor(self).add_subprocess(IdentifyCompletedTaskAgendaProcessor(self)))
        agenda.add_subprocess(IdentifyPreconditionSatisfyingActionsAgendaProcessor(self))
        agenda.add_subprocess(FRResolutionAgendaProcessor())
        agenda.add_subprocess(IdentifyPreconditionsAgendaProcessor(self))
        agenda.add_subprocess(HandleRequestedActionsAgendaProcessor(self))
        agenda.add_subprocess(HandleCurrentActionAgendaProcessor(self))
        agenda.add_subprocess(RecognizeSubEventsAgendaProcessor(self).add_subprocess(RecognizePartsOfObjectAgendaProcessor(self)))
        agenda.add_subprocess(IdentifyClosingOfUnknownTaskAgendaProcessor(self))

        return agenda

    # ------ Meta-contextual Properties -------

    LEARNING = "*LCT.learning"          # Marks an event that is being learned; True / False (absent)
    LEARNED = "*LCT.learned"            # Marks an event that has been learned; True / False (absent)
    CURRENT = "*LCT.current"            # Marks an event that is currently being explained; True / False (absent)
    WAITING_ON = "*LCT.waiting_on"      # Marks an event that is waiting on another event to be explained; FR EVENT ID
    FROM_CONTEXT = "*LCT.from_context"  # Marks an instance as having been moved to LT memory from a particular LCT context (as an ID)

    # ------ Context Helper Functions -------

    # Helper function for returning the learning hierarchy; starting with LTC.current, and finding each "parent"
    # via the LCT.waiting_on property; the names are returned in that order (element 0 is current).
    def learning_hierarchy(self):
        results = self.agent.wo_memory.search(context={LCTContext.LEARNING: True, LCTContext.CURRENT: True})
        if len(results) != 1:
            return []

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