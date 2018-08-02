from backend.contexts.LCTContext import LCTContext
from backend.models.agenda import Action, Agenda, Goal, Variable
from backend.models.fr import FR
from backend.models.graph import Literal, Network
from backend.models.ontology import Ontology
from backend.models.tmr import TMR
from backend.utils.AgentLogger import AgentLogger
from typing import Union


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
        print("PRE:")
        print(self.internal)

        self._input(input)
        print("I:")
        print(self.internal)

        self._decision()
        print("D:")
        print(self.internal)

        self._execute()
        print("E:")
        print(self.internal)

        self._assess()
        print("A:")
        print(self.internal)

    def _input(self, input: Union[dict, TMR]=None):
        if input is None:
            return

        if isinstance(input, dict):
            input = TMR(input, ontology=self.ontology)

        tmr = self.register(input)
        # self.input_memory.append(tmr)

        frame = self.internal.register("INPUT-TMR")
        frame["REFERS-TO-GRAPH"] = Literal(tmr._namespace)
        frame["ACKNOWLEDGED"] = False
        self.identity["HAS-INPUT"] = frame

        self._logger.log("Input: '" + tmr.sentence + "'")

    def _decision(self):
        agenda = self.agenda()

        priority = -1.0
        selected = None
        for goal in agenda.goals(pending=True, active=True):
            goal.prioritize(self)
            if goal.priority() > priority:
                priority = goal.priority()
                selected = goal
        if selected is not None:
            selected.status(Goal.Status.ACTIVE)
            agenda.prepare_action(selected.pursue(self))

    def _execute(self):
        self.agenda().action().execute(self)
        del self.agenda().frame["ACTION-TO-TAKE"]

    def _assess(self):
        for active in self.agenda().goals():
            active.assess()

    def agenda(self):
        return Agenda(self.identity)

    def pending_inputs(self):
        inputs = map(lambda input: input.resolve(), self.identity["HAS-INPUT"])
        inputs = filter(lambda input: input["ACKNOWLEDGED"] == False, inputs)
        inputs = map(lambda input: input["REFERS-TO-GRAPH"][0].resolve().value, inputs)
        inputs = map(lambda input: self[input], inputs)
        return list(inputs)

    def _augment_ontology(self):
        # This is a temporary means of modifying the starting condition of the test agent; these changes should
        # be moved into an instance of the ontology (database), in the long-term.

        # Define the agenda (it is not a unique concept, but rather, a series of properties used on anything that
        # can have an agenda).  It uses the existing GOAL relation to point to AGENDA-GOAL instances (below).
        self.ontology.register("ACTION-TO-TAKE", isa="ONT.RELATION")  # range = ACTION

        # Define goals on the agenda, and their properties
        self.ontology.register("AGENDA-GOAL", isa="ONT.ABSTRACT-IDEA")
        self.ontology.register("GOAL-RELATION", isa="ONT.RELATION")
        self.ontology.register("ON-CONDITION", isa="ONT.GOAL-RELATION")  # range = GOAL-CONDITION
        self.ontology.register("PRIORITY-CALCULATION", isa="ONT.GOAL-RELATION")  # range = MEANING-PROCEDURE
        self.ontology.register("ACTION-SELECTION", isa="ONT.GOAL-RELATION")      # range = MEANING-PROCEDURE
        self.ontology.register("GOAL-ATTRIBUTE", isa="ONT.LITERAL-ATTRIBUTE")
        self.ontology.register("STATUS", isa="ONT.GOAL-ATTRIBUTE")  # pending, active, abandoned, satisfied
        self.ontology.register("PRIORITY", isa="ONT.GOAL-ATTRIBUTE")  # 0 - 1

        # Define actions an agent can take, and their properties
        self.ontology.register("ACTION", isa="ONT.EVENT")
        self.ontology.register("RUN", isa="ONT.RELATION")  # range = MEANING-PROCEDURE

        # Define status changing conditions a goal can have
        self.ontology.register("GOAL-CONDITION", isa="ONT.ALGORITHM")
        self.ontology.register("WITH-CONDITION", isa="ONT.RELATION")  # range = PROPERTY
        self.ontology.register("LOGIC", isa="ONT.LITERAL-ATTRIBUTE")  # and, or, not
        self.ontology.register("APPLY-STATUS", isa="ONT.STATUS")  # (from above: pending, active, abandoned, satisfied)
        # (also uses ORDER) from above

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

        # Define inputs, and their properties
        self.ontology.register("INPUT-TMR", isa="ONT.ABSTRACT-OBJECT")
        self.ontology.register("REFERS-TO-GRAPH", isa="ONT.LITERAL-ATTRIBUTE")  # The namespace of a graph in the network
        self.ontology.register("ACKNOWLEDGED", isa="ONT.LITERAL-ATTRIBUTE")  # True / False
        self.ontology.register("HAS-INPUT", isa="ONT.RELATION")  # range = INPUT-TMR; applied to self.identity to track inputs

        # Define a base goal and actions (FIND-SOMETHING-TO-DO, IDLE, and ACKNOWLEDGE-INPUT)
        self.ontology.register("FIND-SOMETHING-TO-DO", isa="ONT.AGENDA-GOAL")
        self.ontology["FIND-SOMETHING-TO-DO"]["PRIORITY-CALCULATION"] = "ONT.FIND-SOMETHING-TO-DO-PRIORITY"
        self.ontology["FIND-SOMETHING-TO-DO"]["ACTION-SELECTION"] = "ONT.FIND-SOMETHING-TO-DO-ACTION"
        self.ontology["FIND-SOMETHING-TO-DO"]["ON-CONDITION"] = "ONT.FIND-SOMETHING-TO-DO-CONDITION"

        self.ontology.register("FIND-SOMETHING-TO-DO-PRIORITY", isa="ONT.MEANING-PROCEDURE")
        self.ontology["FIND-SOMETHING-TO-DO-PRIORITY"]["CALLS"] = Literal("find_something_to_do_priority")

        self.ontology.register("FIND-SOMETHING-TO-DO-ACTION", isa="ONT.MEANING-PROCEDURE")
        self.ontology["FIND-SOMETHING-TO-DO-ACTION"]["CALLS"] = Literal("find_something_to_do_action")

        self.ontology.register("ONT.FIND-SOMETHING-TO-DO-CONDITION", isa="ONT.GOAL-CONDITION")
        self.ontology["ONT.FIND-SOMETHING-TO-DO-CONDITION"]["APPLY-STATUS"] = Literal(Goal.Status.PENDING.name)

        self.ontology.register("IDLE", isa="ONT.ACTION")
        self.ontology["IDLE"]["RUN"] = "IDLE-MP"

        self.ontology.register("IDLE-MP", isa="ONT.MEANING-PROCEDURE")
        self.ontology["IDLE-MP"]["CALLS"] = Literal("idle")
        self.ontology["IDLE-MP"]["ORDER"] = 1

        self.ontology.register("ACKNOWLEDGE-INPUT", isa="ONT.ACTION")
        self.ontology["ACKNOWLEDGE-INPUT"]["RUN"] = "ACKNOWLEDGE-INPUT-MP"

        self.ontology.register("ACKNOWLEDGE-INPUT-MP", isa="ONT.MEANING-PROCEDURE")
        self.ontology["ACKNOWLEDGE-INPUT-MP"]["CALLS"] = Literal("acknowledge-input")
        self.ontology["ACKNOWLEDGE-INPUT-MP"]["ORDER"] = 1

        # Define a goal and action for understanding input
        self.ontology.register("UNDERSTAND-INPUT", isa="ONT.AGENDA-GOAL")
        self.ontology["UNDERSTAND-INPUT"]["PRIORITY-CALCULATION"] = "ONT.UNDERSTAND-INPUT-PRIORITY"
        self.ontology["UNDERSTAND-INPUT"]["ACTION-SELECTION"] = "ONT.UNDERSTAND-INPUT-ACTION"
        self.ontology["UNDERSTAND-INPUT"]["ON-CONDITION"] = "ONT.UNDERSTAND-INPUT-CONDITION"

        self.ontology.register("UNDERSTAND-INPUT-PRIORITY", isa="ONT.MEANING-PROCEDURE")
        self.ontology["UNDERSTAND-INPUT-PRIORITY"]["CALLS"] = Literal("understand_input_priority")

        self.ontology.register("UNDERSTAND-INPUT-ACTION", isa="ONT.MEANING-PROCEDURE")
        self.ontology["UNDERSTAND-INPUT-ACTION"]["CALLS"] = Literal("understand_input_action")

        self.ontology.register("ONT.UNDERSTAND-INPUT-CONDITION", isa="ONT.GOAL-CONDITION")
        self.ontology["ONT.UNDERSTAND-INPUT-CONDITION"]["WITH-CONDITION"] = "ONT.UNDERSTAND-INPUT-WITH-CONDITION"
        self.ontology["ONT.UNDERSTAND-INPUT-CONDITION"]["APPLY-STATUS"] = Literal(Goal.Status.SATISFIED.name)

        self.ontology.register("UNDERSTAND", isa="ONT.ACTION")
        self.ontology["UNDERSTAND"]["RUN"] = "UNDERSTAND-MP"

        self.ontology.register("UNDERSTAND-MP", isa="ONT.MEANING-PROCEDURE")
        self.ontology["UNDERSTAND-MP"]["CALLS"] = Literal("understand_input_action")
        self.ontology["UNDERSTAND-MP"]["ORDER"] = 1

        self.ontology.register("ONT.UNDERSTAND-INPUT-WITH-CONDITION", isa="ONT.ACKNOWLEDGED")
        self.ontology.register("DOMAIN", Variable("X"))
        self.ontology.register("RANGE", True)


    def _bootstrap(self):
        # Initializes the agent's current memory and environment, if any.

        goal = self.internal.register("FIND-SOMETHING-TO-DO", isa="ONT.FIND-SOMETHING-TO-DO")
        Goal(goal).inherit()

        self.identity["GOAL"] += goal

        def acknowledge_input(agent):
            inputs = agent.pending_inputs()
            if len(inputs) == 0:
                return
            # TODO: here is where we need to note that inputs[0] is a variable (specifically, it is "X" in the condition, and also needed for the action)
            goal = agent.internal.register("UNDERSTAND-INPUT", isa="ONT.UNDERSTAND-INPUT")
            Goal(goal).inherit()
            agent.identity["GOAL"] += goal

        def understand_input(agent):
            print("WE NEED VARIABLES HERE TOO")
            # TODO: HACK, use variables to select just one
            for i in agent.pending_inputs():
                i["ACKNOWLEDGED"] = True

        from backend.models.mps import MPRegistry
        MPRegistry.register(lambda agent: 0.1, name="find_something_to_do_priority")
        MPRegistry.register(lambda agent: self.ontology["IDLE"] if len(self.pending_inputs()) == 0 else self.ontology["ACKNOWLEDGE-INPUT"], "find_something_to_do_action")
        MPRegistry.register(lambda agent: print("ZZZZ"), "idle")
        MPRegistry.register(acknowledge_input, name="acknowledge-input")
        MPRegistry.register(lambda agent: 0.9, name="understand_input_priority")
        MPRegistry.register(lambda agent: self.ontology["UNDERSTAND"], name="understand_input_action")
        MPRegistry.register(understand_input, name="understand_input_action")
