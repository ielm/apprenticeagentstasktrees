from backend.contexts.LCTContext import LCTContext
from backend.models.agenda import Action, Agenda, Goal
from backend.models.fr import FR
from backend.models.graph import Literal, Network
from backend.models.ontology import Ontology
from backend.models.statement import Statement
from backend.models.tmr import TMR
from backend.utils.AgentLogger import AgentLogger
from enum import Enum
from typing import Union

import sys


class Agent(Network):

    def __init__(self, ontology: Ontology=None):
        super().__init__()

        if ontology is None:
            raise Exception("NYI, Default Ontology Required")

        self.exe = self.register(Statement.hierarchy())
        self.ontology = self.register(ontology)

        self.internal = self.register(FR("SELF", self.ontology))
        self.wo_memory = self.register(FR("WM", self.ontology))
        self.lt_memory = self.register(FR("LT", self.ontology))

        self.identity = self.internal.register("ROBOT")
        self.exe.register("INPUT-TMR", generate_index=False)
        self._bootstrap()

        self.input_memory = []
        self.action_queue = []
        self.context = LCTContext(self)

        self._logger = AgentLogger()
        self.wo_memory.logger(self._logger)
        self.lt_memory.logger(self._logger)

    def logger(self, logger=None):
        if logger is not None:
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

    def iidea(self, input=None): # (I)ndependent (I)nput, (D)ecide + (E)xecute + (A)ssess
        global iidea_stage

        if input is not None:
            self._input(input)

        Agent.IDEA.get_method()(self)
        Agent.IDEA.advance()

        print("T" + str(Agent.IDEA.time()) + " " + Agent.IDEA.stage())
        print(self.internal)

    def _input(self, input: Union[dict, TMR]=None):
        if input is None:
            return

        if isinstance(input, dict):
            input = TMR(input, ontology=self.ontology)

        tmr = self.register(input)

        frame = self.internal.register("INPUT-TMR", isa="EXE.INPUT-TMR", generate_index=True)
        frame["REFERS-TO-GRAPH"] = Literal(tmr._namespace)
        frame["ACKNOWLEDGED"] = False
        self.identity["HAS-INPUT"] += frame

        self._logger.log("Input: '" + tmr.sentence + "'")

    def _decision(self):
        agenda = self.agenda()

        priority_weight = self.identity["PRIORITY_WEIGHT"].singleton()
        resources_weight = self.identity["RESOURCES_WEIGHT"].singleton()

        decision = -sys.maxsize
        selected = None

        for goal in agenda.goals(pending=True, active=True):
            goal.status(Goal.Status.PENDING)
            _priority = goal.priority(self)
            _resources = goal.resources(self)
            _decision = (_priority * priority_weight) - (_resources * resources_weight)
            goal.decision(decide=_decision)

            if _decision > decision:
                decision = _decision
                selected = goal

        if selected is not None:
            selected.status(Goal.Status.ACTIVE)
            agenda.prepare_action(selected.plan())

    def _execute(self):
        goal = self.agenda().goals(active=True)[0]
        self.agenda().action().perform(goal)
        del self.agenda().frame["ACTION-TO-TAKE"]

    def _assess(self):
        for active in self.agenda().goals():
            active.assess()

    def agenda(self):
        return Agenda(self.identity)

    def pending_inputs(self):
        inputs = map(lambda input: input.resolve(), self.identity["HAS-INPUT"])
        inputs = filter(lambda input: input["ACKNOWLEDGED"] == False, inputs)
        inputs = map(lambda input: input["REFERS-TO-GRAPH"].singleton(), inputs)
        inputs = map(lambda input: self[input], inputs)
        return list(inputs)

    def _bootstrap(self):

        from backend.models.bootstrap import Bootstrap
        Bootstrap.bootstrap_resource(self, "backend.resources", "goals.aa")
        Bootstrap.bootstrap_resource(self, "backend.resources", "bootstrap.knowledge")

        self.agenda().add_goal(Goal.instance_of(self.internal, self.exe["FIND-SOMETHING-TO-DO"], []))

        from backend.models.mps import MPRegistry

        def understand_input(statement, tmr_frame):
            tmr = self[tmr_frame["REFERS-TO-GRAPH"].singleton()]
            agenda = self.context.default_understanding()
            agenda.logger(self._logger)
            agenda.process(self, tmr)

        MPRegistry.register(understand_input)

        def prioritize_learning(statement, tmr_frame):
            return 0.75
        MPRegistry.register(prioritize_learning)


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

