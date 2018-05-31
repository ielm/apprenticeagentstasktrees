from backend.contexts.context import AgentContext, RootAgendaProcessor
from backend.heuristics.actcontext.act_agenda_heuristics import *
from backend.ontology import Ontology


# An agent context for (A)cting on (C)omplex (T)asks.
class ACTContext(AgentContext):

    def __init__(self, agent):
        super().__init__(agent)

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

        agenda.add_subprocess(RecallTaskFromLongTermMemoryAgendaProcessor(self).add_subprocess(QueuePreconditionActionsAgendaProcessor(self)))

        return agenda

        # ------ Meta-contextual Properties -------

    DOING = "*ACT.doing"  # Marks an event that is being targeted to "do".