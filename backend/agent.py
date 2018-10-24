from backend.contexts.LCTContext import LCTContext
from backend.models.agenda import Action, Agenda, Goal
from backend.models.effectors import Callback, Capability, Effector
from backend.models.fr import FR
from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from backend.models.mps import MPRegistry
from backend.models.ontology import Ontology
from backend.models.statement import CapabilityStatement, Statement, VariableMap
from backend.models.tmr import TMR
from backend.utils.AgentLogger import AgentLogger
from enum import Enum
from typing import Callable, List, Union

import sys


class Agent(Network):
    """
    The Agent
    """

    def __init__(self, ontology: Ontology = None):
        """
        Initialize Agent

        :param ontology: The agent's "World Model"
        """
        super().__init__()

        if ontology is None:
            raise Exception("NYI, Default Ontology Required")

        self.exe = self.register(Statement.hierarchy())
        self.ontology = self.register(ontology)

        self.internal = self.register(FR("SELF", self.ontology))
        self.wo_memory = self.register(FR("WM", self.ontology))
        self.lt_memory = self.register(FR("LT", self.ontology))
        self.environment = self.register(FR("ENV", self.ontology))

        self.identity = self.internal.register("ROBOT", isa="ONT.ROBOT")
        self.exe.register("INPUT-TMR", generate_index=False)
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

        agenda = self.context.default_understanding()
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

    class IDEA(object):
        D = 1
        E = 2
        A = 3

        _stage = D
        _time = 1

        @classmethod
        def get_method(cls):
            if Agent.IDEA._stage == Agent.IDEA.D:
                return Agent._decision
            if Agent.IDEA._stage == Agent.IDEA.E:
                return Agent._execute
            if Agent.IDEA._stage == Agent.IDEA.A:
                return Agent._assess

        @classmethod
        def advance(cls):
            if Agent.IDEA._stage == Agent.IDEA.D:
                Agent.IDEA._stage = Agent.IDEA.E
                return

            if Agent.IDEA._stage == Agent.IDEA.E:
                Agent.IDEA._stage = Agent.IDEA.A
                return

            if Agent.IDEA._stage == Agent.IDEA.A:
                Agent.IDEA._stage = Agent.IDEA.D
                Agent.IDEA._time += 1
                return

        @classmethod
        def stage(cls) -> str:
            if Agent.IDEA._stage == Agent.IDEA.D:
                return "Decide"
            if Agent.IDEA._stage == Agent.IDEA.E:
                return "Execute"
            if Agent.IDEA._stage == Agent.IDEA.A:
                return "Assess"

        @classmethod
        def time(cls) -> int:
            return Agent.IDEA._time

    def iidea(self, input=None):
        """
        (I)ndependent (I)nput, (D)ecide + (E)xecute + (A)ssess

        :param input: Input for iidea loop
        """
        global iidea_stage

        if input is not None:
            self._input(input)

        Agent.IDEA.get_method()(self)
        Agent.IDEA.advance()

        print("T" + str(Agent.IDEA.time()) + " " + Agent.IDEA.stage())
        print(self.internal)

    def _input(self, input: Union[dict, TMR] = None):
        if input is None:
            return

        # Create TMR with input dict()
        if isinstance(input, dict):
            input = TMR(input, ontology=self.ontology)

        # Register TMR as a new graph in self._storage
        tmr = self.register(input)

        # Set var frame as registered "INPUT-TMR" in self.internal graph.
        frame = self.internal.register("INPUT-TMR", isa="EXE.INPUT-TMR", generate_index=True)
        # The frame "INPUT-TMR" regers to the input TMR
        frame["REFERS-TO-GRAPH"] = Literal(tmr._namespace)
        # Frame has not been acknowledged yet
        frame["ACKNOWLEDGED"] = False
        # Add frame to ROBOT["HAS-INPUT"].
        # ATTN - Does ROBOT["HAS-INPUT"] contain all past inputs?
        self.identity["HAS-INPUT"] += frame

        self._logger.log("Input: '" + tmr.sentence + "'")

    def _decision(self):
        agenda = self.agenda()

        priority_weight = self.identity["PRIORITY_WEIGHT"].singleton()
        resources_weight = self.identity["RESOURCES_WEIGHT"].singleton()

        goals = agenda.goals(pending=True, active=True)
        for goal in goals:
            _priority = goal.priority(self)
            _resources = goal.resources(self)
            _decision = (_priority * priority_weight) - (_resources * resources_weight)
            goal.decision(decide=_decision)

        ordered = sorted(goals, key=lambda g: g.decision(), reverse=True)
        effectors = self.effectors()

        for goal in ordered:
            action = goal.plan()
            capabilities = action.capabilities()

            assigned_effectors = []
            for capability in capabilities:
                for effector in filter(lambda e: e.is_free() and not e in assigned_effectors, effectors):
                    if capability in effector.capabilities():
                        assigned_effectors.append(effector)
                        break

            if len(capabilities) != len(assigned_effectors):
                continue

            goal.status(Goal.Status.ACTIVE)
            agenda.prepare_action(action)

            for i, effector in enumerate(assigned_effectors):
                effector.reserve(goal, capabilities[i])

    def _execute(self):
        goal = self.agenda().goals(active=True)[0]
        # self.agenda().action().perform(goal)
        for action in self.agenda().action():
            action.perform(goal)
        del self.agenda().frame["ACTION-TO-TAKE"]

    def _assess(self):
        for active in self.agenda().goals():
            active.assess()

    def agenda(self):
        return Agenda(self.identity)

    def effectors(self) -> List[Effector]:
        return list(map(lambda e: Effector(e.resolve()), self.identity["HAS-EFFECTOR"]))

    def pending_inputs(self):
        inputs = map(lambda input: input.resolve(), self.identity["HAS-INPUT"])
        inputs = filter(lambda input: input["ACKNOWLEDGED"] == False, inputs)
        inputs = map(lambda input: input["REFERS-TO-GRAPH"].singleton(), inputs)
        inputs = map(lambda input: self[input], inputs)
        return list(inputs)

    def callback(self, callback: Union[str, Identifier, Frame, 'Callback']):
        if isinstance(callback, Callback):
            callback = callback.frame
        if isinstance(callback, Frame):
            callback = callback._identifier

        if callback not in self.exe:
            return

        if isinstance(callback, str):
            callback = Callback(self.exe[callback])
        if isinstance(callback, Identifier):
            callback = Callback(self.exe[callback])

        callback.run()
        del self.exe[callback.frame.name()]

    def _bootstrap(self):
        # ATTN - Should these be declared somewhere else for cleanliness? If so, where? backend.resources.goals?
        # TODO - Rewrite logic for input understanding
        def understand_input(statement, tmr_frame, callback=None):
            tmr = self[tmr_frame["REFERS-TO-GRAPH"].singleton()]
            agenda = self.context.default_understanding()
            agenda.logger(self._logger)
            agenda.process(self, tmr)
            if callback is not None:
                self.callback(callback)

            if callback is not None:
                self.callback(callback)

        MPRegistry.register(understand_input)

        # TODO - write logic for learning prioritization
        def prioritize_learning(statement, tmr_frame):
            return 0.75

        MPRegistry.register(prioritize_learning)

        # TODO - write logic for resource evaluation
        def evaluate_resources(statement, tmr_frame):
            return 0.5

        MPRegistry.register(evaluate_resources)

        # TODO - write logic for acknowledging input
        def acknowledge_input(statement, input, callback=None):
            # Input should be frame that tells you name of graph
            # Is it language input or visual input
            # Is it of sufficient interest?
            #     Mark as acknowledged
            # Else mark as ignored -> tmr["STATUS"] = "IGNORED"
            return

        MPRegistry.register(acknowledge_input)

        def decide_on_language_input(statement, input, callback=None):
            """
            DECIDE-ON-LANGUAGE-INPUT is a goal that determines what to do with an input of sufficient interest.  It can do several things after determining the nature of the input.
            - If the input appears to be a request for action of a complex task (such as building a chair)
                - a new instance of PERFORM-COMPLEX-TASK will be created.
            - If the input appears to be a request for information (a question or query)
                - a new instance of RESPOND-TO-QUERY will be created.
            - It can also determine that it needs to learn from input, in other words, the previous demo

            :param statement:
            :param input:
            :return:
            """
            # print(input._frame_type()._ISA_type())
            return

        MPRegistry.register(decide_on_language_input)

        from backend.models.bootstrap import Bootstrap
        Bootstrap.bootstrap_resource(self, "backend.resources", "bootstrap.knowledge")
        Bootstrap.bootstrap_resource(self, "backend.resources", "goals.aa")

        self.agenda().add_goal(Goal.instance_of(self.internal, self.exe["FIND-SOMETHING-TO-DO"], []))

        # API declared versions of the two goal definitions

        # graph = self["EXE"]

        # goal1 = Goal.define(graph, "FIND-SOMETHING-TO-DO", 0.1, [
        #     Action.build(graph,
        #                  "acknowledge input",
        #                  ExistsStatement.instance(graph, Query.parse(self, "WHERE (@^ EXE.INPUT-TMR AND ACKNOWLEDGED = False)")),
        #                  ForEachStatement.instance(graph, Query.parse(self, "WHERE (@^ EXE.INPUT-TMR AND ACKNOWLEDGED = False)"), "$tmr",  [
        #                      AddFillerStatement.instance(graph, self.identity, "HAS-GOAL",
        #                                                  MakeInstanceStatement.instance(graph, "SELF", "EXE.UNDERSTAND-TMR", ["$tmr"])),
        #                      AssignFillerStatement.instance(graph, "$tmr", "ACKNOWLEDGED", True)
        #                      ])
        #                  ),
        #     Action.build(graph, "idle", Action.DEFAULT, Action.IDLE)
        # ], [], [])

        # goal2 = Goal.define(graph, "UNDERSTAND-TMR", 0.9, [
        #     Action.build(graph,
        #                  "understand",
        #                  Action.DEFAULT,
        #                  [
        #                      MeaningProcedureStatement.instance(graph, "understand_input", ["$tmr"]),
        #                      AssignFillerStatement.instance(graph, "$tmr", "STATUS", Literal("UNDERSTOOD"))
        #                  ])
        # ], [
        #     Condition.build(graph,
        #                     [IsStatement.instance(graph, "$tmr", "STATUS", Literal("UNDERSTOOD"))],
        #                     Goal.Status.SATISFIED)
        # ], ["$tmr"])
