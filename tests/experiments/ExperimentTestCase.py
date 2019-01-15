from backend.agent import Agent
from backend.models.agenda import Decision, Expectation, Goal, Plan, Step
from backend.models.effectors import Callback, Effector
from backend.models.graph import Frame, Identifier
from backend.models.mps import AgentMethod
from backend.models.output import OutputXMR

from pkgutil import get_data
from typing import Callable, List, Type, Union
from unittest.mock import patch

import json
import unittest


class ExperimentTestCase(unittest.TestCase):

    def setUp(self):
        from backend.models.tmr import TMR
        from backend.models.vmr import VMR
        from backend.utils.AtomicCounter import AtomicCounter

        TMR.counter = AtomicCounter()
        VMR.counter = AtomicCounter()
        Agent.IDEA.reset()

    @staticmethod
    def analyses():
        return json.loads(get_data("tests.resources", "Example_Analyses.json").decode('ascii'))

    @staticmethod
    def iidea_loop(agent: Agent, mock: Type[AgentMethod]=None):
        if mock is not None:
            print(mock)

        def __iidea(agent: Agent):
            if agent.IDEA._stage == Agent.IDEA.D:
                agent.iidea()
            while agent.IDEA._stage != Agent.IDEA.D:
                agent.iidea()

        if mock is None:
            __iidea(agent)
        else:
            with patch.object(mock, 'run') as m:
                __iidea(agent)
                return m

    def assertGoalExists(self, agent: Agent, isa: str=None, status: Goal.Status=None, query: Callable=None):
        goals = list(map(lambda g: Goal(g.resolve()), agent.identity["HAS-GOAL"]))

        if status is not None:
            goals = agent.agenda().goals(pending=(status == Goal.Status.PENDING), active=(status == Goal.Status.ACTIVE), abandoned=(status == Goal.Status.ABANDONED), satisfied=(status == Goal.Status.SATISFIED))

        if isa is not None:
            goals = list(filter(lambda goal: goal.frame ^ isa, goals))

        if query is not None:
            goals = list(filter(query, goals))

        if len(goals) == 0:
            self.fail("No such matching goal.")

    def assertDecisionExists(self, agent: Agent, status: Decision.Status=None, goal: [str, Identifier, Frame, Goal]=None, plan: [str, Identifier, Frame, Plan]=None, step: [str, Identifier, Frame, Step]=None, outputs: List[Union[str, Identifier, Frame, OutputXMR]]=None, effectors: List[Union[str, Identifier, Frame, Effector]]=None, callbacks: List[Union[str, Identifier, Frame, Callback]]=None, impasses: List[Union[str, Identifier, Frame, Goal]]=None, expectations: List[Union[str, Identifier, Frame, Expectation]]=None, query: Callable=None):

        if isinstance(goal, str):
            goal = Identifier.parse(goal)
        if isinstance(goal, Identifier):
            goal = agent.lookup(goal)
        if isinstance(goal, Frame):
            goal = Goal(goal)

        if isinstance(plan, str):
            plan = Identifier.parse(plan)
        if isinstance(plan, Identifier):
            plan = agent.lookup(plan)
        if isinstance(plan, Frame):
            plan = Plan(plan)

        if isinstance(step, str):
            step = Identifier.parse(step)
        if isinstance(step, Identifier):
            step = agent.lookup(step)
        if isinstance(step, Frame):
            step = Step(step)

        if outputs is not None:

            def convert_output(output):
                if isinstance(output, str):
                    output = Identifier.parse(output)
                if isinstance(output, Identifier):
                    output = agent.lookup(output)
                if isinstance(output, Frame):
                    output = OutputXMR(output)
                return output

            outputs = list(map(lambda output: convert_output(output), outputs))

        if effectors is not None:

            def convert_effector(effector):
                if isinstance(effector, str):
                    effector = Identifier.parse(effector)
                if isinstance(effector, Identifier):
                    effector = agent.lookup(effector)
                if isinstance(effector, Frame):
                    effector = Effector(effector)
                return effector

            effectors = list(map(lambda effector: convert_effector(effector), effectors))

        if callbacks is not None:

            def convert_callback(callback):
                if isinstance(callback, str):
                    callback = Identifier.parse(callback)
                if isinstance(callback, Identifier):
                    callback = agent.lookup(callback)
                if isinstance(callback, Frame):
                    callback = Callback(callback)
                return callback

            callbacks = list(map(lambda callback: convert_callback(callback), callbacks))

        if impasses is not None:

            def convert_impasse(impasse):
                if isinstance(impasse, str):
                    impasse = Identifier.parse(impasse)
                if isinstance(impasse, Identifier):
                    impasse = agent.lookup(impasse)
                if isinstance(impasse, Frame):
                    impasse = Goal(impasse)
                return impasse

            impasses = list(map(lambda impasse: convert_impasse(impasse), impasses))

        if expectations is not None:

            def convert_expectation(expectation):
                if isinstance(expectation, str):
                    expectation = Identifier.parse(expectation)
                if isinstance(expectation, Identifier):
                    expectation = agent.lookup(expectation)
                if isinstance(expectation, Frame):
                    expectation = Expectation(expectation)
                return expectation

            expectations = list(map(lambda expectation: convert_expectation(expectation), expectations))

        decisions = agent.decisions()

        if status is not None:
            decisions = list(filter(lambda decision: decision.status() == status, decisions))

        if goal is not None:
            decisions = list(filter(lambda decision: decision.goal() == goal, decisions))

        if plan is not None:
            decisions = list(filter(lambda decision: decision.plan() == plan, decisions))

        if step is not None:
            decisions = list(filter(lambda decision: decision.step() == step, decisions))

        if outputs is not None:
            decisions = list(filter(lambda decision: decision.outputs() == outputs, decisions))

        if effectors is not None:
            decisions = list(filter(lambda decision: decision.effectors() == effectors, decisions))

        if callbacks is not None:
            decisions = list(filter(lambda decision: decision.callbacks() == callbacks, decisions))

        if impasses is not None:
            decisions = list(filter(lambda decision: decision.impasses() == impasses, decisions))

        if expectations is not None:
            decisions = list(filter(lambda decision: decision.expectations() == expectations, decisions))

        if query is not None:
            decisions = list(filter(query, decisions))

        if len(decisions) == 0:
            self.fail("No such matching decision.")