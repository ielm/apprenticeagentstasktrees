from backend.contexts.LCTContext import LCTContext
from backend.models.agenda import Agenda
from backend.models.fr import FR
from backend.models.graph import Network
from backend.models.ontology import Ontology
from backend.models.tmr import TMR
from backend.utils.AgentLogger import AgentLogger


class Agent(Network):

    def __init__(self, ontology: Ontology=None):
        super().__init__()

        if ontology is None:
            raise Exception("NYI, Default Ontology Required")

        self.ontology = self.register(ontology)
        self._augment_ontology()

        self.internal = self.register(FR("SELF", self.ontology))
        self.wo_memory = self.register(FR("WM", self.ontology))
        self.lt_memory = self.register(FR("LT", self.ontology))

        self.identity = self.internal.register("ROBOT")
        self._bootstrap()

        self.input_memory = []
        self.action_queue = []
        self.context = LCTContext(self)

        self._logger = AgentLogger()
        self.wo_memory.logger(self._logger)
        self.lt_memory.logger(self._logger)

    def logger(self, logger=None):
        if not logger is None:
            self._logger = logger
        return self._logger

    def input(self, input):
        tmr = self.register(TMR(input, ontology=self.ontology))
        self.input_memory.append(tmr)

        self._logger.log("Input: '" + tmr.sentence + "'")

        agenda = self.context.default_agenda()
        agenda.logger(self._logger)
        agenda.process(self, tmr)

    def idea(self, input):
        tmr = self.register(TMR(input, ontology=self.ontology))
        self.input_memory.append(tmr)
        self._logger.log("Input: '" + tmr.sentence + "'")

        agenda = self.agenda()

    def agenda(self):
        return Agenda(self.identity)

    def _augment_ontology(self):
        # This is a temporary means of modifying the starting condition of the test agent; these changes should
        # be moved into an instance of the ontology (database), in the long-term.

        # Define the agenda (it is not a unique concept, but rather, a series of properties used on anything that
        # can have an agenda).  It uses the existing GOAL relation to point to AGENDA-GOAL instances (below).
        self.ontology.register("ACTION-TO-TAKE", isa="ONT.RELATION")  # range = ACTION

        # Define goals on the agenda, and their properties
        self.ontology.register("AGENDA-GOAL", isa="ONT.ABSTRACT-IDEA")
        self.ontology.register("GOAL-RELATION", isa="ONT.RELATION")
        self.ontology.register("GOAL-STATE", isa="ONT.GOAL-RELATION")  # range = PROPERTY
        self.ontology.register("PRIORITY-CALCULATION", isa="ONT.GOAL-RELATION")  # range = MEANING-PROCEDURE
        self.ontology.register("ACTION-SELECTION", isa="ONT.GOAL-RELATION")      # range = MEANING-PROCEDURE
        self.ontology.register("GOAL-ATTRIBUTE", isa="ONT.LITERAL-ATTRIBUTE")
        self.ontology.register("STATUS", isa="ONT.GOAL-ATTRIBUTE")  # pending, active, abandoned, satisfied

        # Define actions an agent can take, and their properties
        self.ontology.register("ACTION", isa="ONT.EVENT")
        self.ontology.register("RUN", isa="ONT.RELATION")  # range = MEANING-PROCEDURE

        # Define meaning procedures, and their properties
        self.ontology.register("MEANING-PROCEDURE", isa="ONT.ALGORITHM")
        self.ontology.register("CALLS", isa="ONT.LITERAL-OBJECT-ATTRIBUTE")  # method name
        self.ontology.register("ORDER", isa="ONT.LITERAL-ATTRIBUTE")   # 1+; optional; domain includes SIGNAL too
        self.ontology.register("ON-SIGNAL", isa="ONT.RELATION")   # range = SIGNAL

        # Define signals, and their properties
        self.ontology.register("SIGNAL", isa="ONT.ALGORITHM")
        self.ontology.register("CODE", isa="ONT.LITERAL-ATTRIBUTE")  # ok, match, fail, error
        self.ontology.register("ACTION", isa="ONT.LITERAL-ATTRIBUTE")  # halt_all, halt_specific, add_next, add_last
        self.ontology.register("TARGET", isa="ONT.RELATION")  # range = MEANING-PROCEDURE; optional
        # (also uses ORDER) from above

        # Define a base goal and action (FIND-SOMETHING-TO-DO and IDLE)
        self.ontology.register("FIND-SOMETHING-TO-DO", isa="ONT.AGENDA-GOAL")
        self.ontology["FIND-SOMETHING-TO-DO"]["PRIORITY-CALCULATION"] = "FIND-SOMETHING-TO-DO-PRIORITY"
        self.ontology["FIND-SOMETHING-TO-DO"]["ACTION-SELECTION"] = "FIND-SOMETHING-TO-DO-ACTION"

        self.ontology.register("FIND-SOMETHING-TO-DO-PRIORITY", isa="ONT.MEANING-PROCEDURE")
        self.ontology["FIND-SOMETHING-TO-DO-PRIORITY"]["CALLS"] = "find_something_to_do_priority"

        self.ontology.register("FIND-SOMETHING-TO-DO-ACTION", isa="ONT.MEANING-PROCEDURE")
        self.ontology["FIND-SOMETHING-TO-DO-ACTION"]["CALLS"] = "find_something_to_do_action"

        self.ontology.register("IDLE", isa="ONT.ACTION")
        self.ontology["IDLE"]["RUN"] = "IDLE-MP"

        self.ontology.register("IDLE-MP", isa="ONT.MEANING-PROCEDURE")
        self.ontology["IDLE-MP"]["CALLS"] = "idle"
        self.ontology["IDLE-MP"]["ORDER"] = 1

    def _bootstrap(self):
        # Initializes the agent's current memory and environment, if any.

        goal = self.internal.register("FIND-SOMETHING-TO-DO", isa="ONT.FIND-SOMETHING-TO-DO")
        goal["STATUS"] = "pending"

        self.identity["GOAL"] += goal