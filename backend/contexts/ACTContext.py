from backend.contexts.context import AgentContext, RootAgendaProcessor
from backend.heuristics.actcontext.act_agenda_heuristics import *
from backend.models.ontology import OntologyFiller


# An agent context for (A)cting on (C)omplex (T)asks.
class ACTContext(AgentContext):

    def __init__(self, agent):
        super().__init__(agent)

    def prepare_static_knowledge(self):
        self.agent.ontology["FASTEN"]["IS-A"] += OntologyFiller("ASSEMBLE", "VALUE")
        self.agent.ontology["ASSEMBLE"]["IS-A"] += OntologyFiller("BUILD", "VALUE")

        self.agent.ontology.register("BRACKET", isa="ARTIFACT-PART")
        self.agent.ontology.register("DOWEL", isa="ARTIFACT-PART")

    def default_agenda(self):

        agenda = RootAgendaProcessor()

        agenda.add_subprocess(RecallTaskFromLongTermMemoryAgendaProcessor(self).add_subprocess(QueuePreconditionActionsAgendaProcessor(self)))

        return agenda

        # ------ Meta-contextual Properties -------

    DOING = "*ACT.doing"  # Marks an event that is being targeted to "do".