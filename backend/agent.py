# from backend.contexts.LCTContext import LCTContext
from backend.models.agenda import Agenda, Decision, Expectation, Goal, Step
from backend.models.effectors import Callback, Effector
from backend.models.environment import Environment
# from backend.models.fr import FR
# from backend.models.graph import Frame, Graph, Identifier, Network
# from backend.models.ontology import Ontology
from backend.models.statement import TransientFrame
from backend.models.tmr import TMR
from backend.models.vmr import VMR
from backend.models.xmr import XMR
from backend.utils.AgentLogger import AgentLogger, CachedAgentLogger
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Query import IsAComparator, Query
from ontograph.Space import Space
from typing import Any, List, Union


class Network(object): pass
class Ontology(object): pass
class Graph(object): pass


class Agent(Network):
    """
    The Agent
    """

    def __init__(self):
        super().__init__()

        self.exe = Space("EXE")
        self.ontology = Space("ONT")

        self.internal = Space("SELF")
        self.wo_memory = Space("WM")
        self.lt_memory = Space("LT")
        self.environment = Space("ENV")

        self.inputs = Space("INPUTS")
        self.outputs = Space("OUTPUTS")

        self.identity = Frame("@SELF.ROBOT.1").add_parent("@ONT.ROBOT")
        self._bootstrap()

        self.input_memory = []
        self.action_queue = []
        # self.context = LCTContext(self)

        self._logger = CachedAgentLogger()
        # self.wo_memory.logger(self._logger)
        # self.lt_memory.logger(self._logger)

    def logger(self, logger=None) -> AgentLogger:
        if not logger is None:
            self._logger = logger
        return self._logger

    @DeprecationWarning
    def input(self, input):
        tmr = TMR.from_json(self, self.ontology, input)
        self.input_memory.append(tmr)

        self._logger.log("Input: " + tmr.render())

        agenda = self.context.default_understanding()
        agenda.logger(self._logger)
        agenda.process(self, tmr)

    class IDEA(object):
        D = 1
        E = 2
        A = 3

        _stage = D
        _time = 1

        @classmethod
        def get_method(cls):
            if Agent.IDEA._stage == Agent.IDEA.D:
                return Agent._decide
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

        @classmethod
        def reset(cls):
            Agent.IDEA._stage = Agent.IDEA.D
            Agent.IDEA._time = 1

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

    def _input(self, input: dict=None, source: Union[str, Identifier, Frame]=None, type: str=None):
        if input is None:
            return

        # If input is visual input, create VMR, else create tmr and continue
        if type == "VISUAL":
            xmr = VMR.from_json(self, self.ontology, input, source=source)
            xmr.update_environment(self.env())
            xmr.update_memory(self.wo_memory)
        else:
            xmr = TMR.from_json(input, source=source)

        # Takes graph obj and writes it to the network
        # registered_xMR = self.register(input)

        self.identity["HAS-INPUT"] += xmr.frame

        # self._logger.log("Input: " + xmr.render())

    def _decide(self):
        agenda = self.agenda()
        agenda.fire_triggers()

        priority_weight = self.preference("PRIORITY_WEIGHT", 0.5)
        resources_weight = self.preference("RESOURCES_WEIGHT", 0.5)

        goals = agenda.goals(pending=True, active=True)
        for goal in goals:
            for plan in goal.plans():
                if plan.select(goal):
                    step = list(filter(lambda step: step.is_pending(), plan.steps()))[0]

                    existing_decisions = self.decisions()
                    existing_decisions = filter(lambda d: d.goal().frame == goal.frame, existing_decisions)
                    existing_decisions = filter(lambda d: d.plan() == plan, existing_decisions)
                    existing_decisions = filter(lambda d: d.step() == step, existing_decisions)

                    if len(list(existing_decisions)) > 0:
                        continue

                    decision = Decision.build(self.internal, goal, plan, step)
                    self.identity["HAS-DECISION"] += decision.frame

        decisions = list(filter(lambda decision: decision.status() == Decision.Status.PENDING, self.decisions()))
        for decision in decisions:
            decision.inspect()

        decisions = list(filter(lambda decision: decision.status() != Decision.Status.BLOCKED, decisions))

        decisions = sorted(decisions, key=lambda d: (d.priority() * priority_weight) - (d.cost() * resources_weight), reverse=True)
        effectors = self.effectors()

        selected_goals = []
        for decision in decisions:
            effector_map = {}

            for output in decision.outputs():
                candidate_effectors = list(effectors)
                candidate_effectors = list(filter(lambda effector: effector.is_free(), candidate_effectors))
                candidate_effectors = list(filter(lambda effector: output.capability() in effector.capabilities(), candidate_effectors))
                candidate_effectors = list(filter(lambda effector: effector not in effector_map.values(), candidate_effectors))
                if len(candidate_effectors) > 0:
                    effector_map[output.frame.id] = candidate_effectors[0]

            if len(effector_map) == len(decision.outputs()) and decision.goal().frame.id not in selected_goals:
                selected_goals.append(decision.goal().frame.id)
                decision.select()
                for output in effector_map.keys():
                    output = XMR(Frame(output))
                    effector = effector_map[output.frame.id]
                    effector.reserve(decision, output, output.capability())
            else:
                decision.decline()
        for goal in selected_goals:
            Goal(Frame(goal)).status(Goal.Status.ACTIVE)
        for decision in self.decisions():
            if decision.status() == Decision.Status.BLOCKED and decision.goal().is_pending():
                decision.goal().status(Goal.Status.ACTIVE)

    def _execute(self):
        for decision in list(filter(lambda decision: decision.status() == Decision.Status.SELECTED, self.decisions())):
            effectors = list(filter(lambda effector: effector.on_decision() == decision, self.effectors()))
            decision.execute(self, effectors)

    def _assess(self):
        reassess = False

        for decision in self.decisions():
            for callback in decision.callbacks():
                if callback.status() == Callback.Status.RECEIVED:
                    callback.process()

        for decision in self.decisions():
            for expectation in decision.expectations():
                expectation.assess(decision.goal())

        for decision in self.decisions():
            for impasse in decision.impasses():
                if impasse.frame.id not in list(map(lambda g: g.frame.id, self.agenda().goals(pending=True, active=True, abandoned=True, satisfied=True))):
                    self.agenda().add_goal(impasse)

        for decision in list(filter(lambda decision: decision.status() == Decision.Status.EXECUTING, self.decisions())):
            if len(decision.callbacks()) == 0 and len(list(filter(lambda e: e.status() != Expectation.Status.SATISFIED, decision.expectations()))) == 0:
                decision.frame["STATUS"] = Decision.Status.FINISHED
                decision.step().frame["STATUS"] = Step.Status.FINISHED

        for decision in list(filter(lambda decision: decision.status() != Decision.Status.BLOCKED and decision.status() != Decision.Status.EXECUTING and decision.status() != Decision.Status.FINISHED, self.decisions())):
            self.identity["HAS-DECISION"] -= decision.frame
            outputs = decision.outputs()
            for output in outputs:
                output.frame.delete()
            decision.frame.delete()
            for output in outputs:
                output.frame.delete()

        for decision in self.decisions():
            decision.assess_impasses()
            if len(decision.impasses()) == 0 and decision.status() == Decision.Status.BLOCKED:
                decision.frame["STATUS"] = Decision.Status.PENDING

        for active in self.agenda().goals(pending=True, active=True, abandoned=True, satisfied=True):
            status = active.frame["STATUS"].singleton()
            active.assess()
            if status != active.frame["STATUS"].singleton():
                reassess = True

        if reassess:
            self._assess()


        #for transient_frame in self.exe.search(Frame.q(self).isa("EXE.TRANSIENT-FRAME")):
        for transient_frame in Query(IsAComparator("@EXE.TRANSIENT-FRAME")).start():
            if transient_frame.id == "@EXE.TRANSIENT-FRAME":
                continue
            if TransientFrame(transient_frame).is_in_scope():
                continue
            transient_frame.delete()
            # del self.exe[transient_frame.name()]

    def agenda(self):
        return Agenda(self.identity)

    def decisions(self) -> List[Decision]:
        return list(map(lambda decision: Decision(decision), self.identity["HAS-DECISION"]))

    def env(self):
        return Environment(self.environment)

    def effectors(self) -> List[Effector]:
        return list(map(lambda e: Effector(e), self.identity["HAS-EFFECTOR"]))

    def pending_inputs(self) -> List[Graph]:
        inputs = map(lambda input: XMR(input), self.identity["HAS-INPUT"])
        inputs = filter(lambda input: input.status() == XMR.InputStatus.RECEIVED, inputs)
        inputs = map(lambda input: input.graph(), inputs)

        return list(inputs)

    def callback(self, callback: Union[str, Identifier, Frame, 'Callback']):
        if isinstance(callback, str):
            callback = Frame(callback)
        if isinstance(callback, Identifier):
            callback = Frame(callback.id)
        if isinstance(callback, Frame):
            callback = Callback(callback)

        callback.received()

    def preference(self, property: str, default: Any):
        if property in self.identity:
            return self.identity[property].singleton()
        return default

    def _bootstrap(self):
        from backend.utils.AgentOntoLang import AgentOntoLang
        graph.set_ontolang(AgentOntoLang())

        self.load_knowledge("backend.resources", "exe.knowledge")

    def load_knowledge(self, package: str, resource: str):
        from pkgutil import get_data
        input: str = get_data(package, resource).decode('ascii')
        graph.ontolang().run(input)

    def spaces(self) -> List[Space]:
        results = {"EXE", "ONT", "SELF", "WM", "LT", "ENV", "INPUTS", "OUTPUTS"}
        results = results.union(set(map(lambda s: s.name, graph)))
        return list(map(lambda s: Space(s), results))

    def __len__(self):
        return len(self.spaces())

    def __iter__(self):
        for space in self.spaces():
            yield space