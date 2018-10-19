from backend.contexts.context import AgentContext, RootUnderstandingProcessor
from backend.heuristics.actcontext.act_agenda_heuristics import *
from backend.models.ontology import OntologyFiller


class ACTContext(AgentContext):
    """
    An agent context for (A)cting on (C)omplex (T)asks.
    """

    def __init__(self, agent):
        """

        :param agent: Agent
        """
        super().__init__(agent)

    def prepare_static_knowledge(self):
        """
        Prepare static knowledge
        """
        self.agent.ontology["FASTEN"]["IS-A"] += OntologyFiller("ASSEMBLE", "VALUE")
        self.agent.ontology["ASSEMBLE"]["IS-A"] += OntologyFiller("BUILD", "VALUE")

        self.agent.ontology.register("BRACKET", isa="ARTIFACT-PART")
        self.agent.ontology.register("DOWEL", isa="ARTIFACT-PART")

    def default_understanding(self):
        """

        :return: understanding
        """
        understanding = RootUnderstandingProcessor()

        understanding.add_subprocess(RecallTaskFromLongTermMemoryUnderstandingProcessor(self).add_subprocess(QueuePreconditionActionsUnderstandingProcessor(self)))

        return understanding

    # ------ Meta-contextual Properties -------

    # Marks an event that is being targeted to "do".
    DOING = "*ACT.doing"