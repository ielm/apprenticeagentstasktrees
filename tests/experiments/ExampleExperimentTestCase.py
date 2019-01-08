from backend.agent import Agent
from backend.models.agenda import Decision, Goal, Plan, Step
from backend.models.bootstrap import Bootstrap
from backend.models.effectors import Callback, Capability, Effector
from backend.models.graph import Identifier, Frame
from backend.models.mps import AgentMethod
from backend.models.ontology import Ontology
from backend.models.output import OutputXMR
from pkgutil import get_data
from typing import Callable, List, Type, Union
from unittest.mock import patch

import json
import unittest


class ExampleExperimentTestCase(unittest.TestCase):

    def setUp(self):
        from backend.models.tmr import TMR
        from backend.utils.AtomicCounter import AtomicCounter

        TMR.counter = AtomicCounter()
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

    def assertDecisionExists(self, agent: Agent, status: Decision.Status=None, goal: [str, Identifier, Frame, Goal]=None, plan: [str, Identifier, Frame, Plan]=None, step: [str, Identifier, Frame, Step]=None, outputs: List[Union[str, Identifier, Frame, OutputXMR]]=None, effectors: List[Union[str, Identifier, Frame, Effector]]=None, callbacks: List[Union[str, Identifier, Frame, Callback]]=None, query: Callable=None):

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

        if query is not None:
            decisions = list(filter(query, decisions))

        if len(decisions) == 0:
            self.fail("No such matching decision.")

    def test_example_throughput(self):

        agent = Agent(ontology=Ontology.init_default())

        # Bootstrap the knowledge
        Bootstrap.bootstrap_resource(agent, "backend.resources.example", "example.knowledge")

        # The agenda is empty
        self.assertEqual(0, len(agent.agenda().goals()))
        self.assertEqual(0, len(agent.decisions()))

        # 0a) Input from "Jake", "Let's build a chair."
        agent._input(self.analyses()[0])

        # 1a) Decide
        agent.iidea()

        # 1b) There is one instance of ACKNOWLEDGE-LANGUAGE-INPUT; it is active, and focused on SELF.XMR.1
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-LANGUAGE-INPUT", status=Goal.Status.ACTIVE, query=lambda goal: goal.resolve("$tmr")._identifier == "INPUTS.XMR.1")

        # 1c) There is one decision, for ACKNOWLEDGE-LANGUAGE-INPUT > acknowledge language input > Step 1; it is selected, and has an output, no effectors, and no callbacks
        self.assertEqual(1, len(agent.decisions()))
        self.assertDecisionExists(agent, status=Decision.Status.SELECTED, goal="SELF.GOAL.1", plan="SELF.PLAN.1", step="SELF.STEP.1", outputs=["OUTPUTS.XMR.1"], effectors=[], callbacks=[])

        # 2a) Execute
        agent.iidea()

        # 2b) There is one instance of ACKNOWLEDGE-LANGUAGE-INPUT; it is active, and focused on SELF.XMR.1
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-LANGUAGE-INPUT", status=Goal.Status.ACTIVE, query=lambda goal: goal.resolve("$tmr")._identifier == "INPUTS.XMR.1")

        # 2c) There is one decision, for ACKNOWLEDGE-LANGUAGE-INPUT > acknowledge language input > Step 1; it is executing, and has an output, an effector, and a callback
        self.assertEqual(1, len(agent.decisions()))
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="SELF.GOAL.1", plan="SELF.PLAN.1", step="SELF.STEP.1", outputs=["OUTPUTS.XMR.1"], effectors=["SELF.MENTAL-EFFECTOR.1"], callbacks=["SELF.CALLBACK.1"])

        # 2d) The decision's callback is received
        self.assertEqual(Callback.Status.RECEIVED, agent.decisions()[0].callbacks()[0].status())

        # 2e) There is one instance of BUILD-A-CHAIR; it is pending
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.PENDING)

        # 2f) The physical effector is free; the mental effector is reserved
        self.assertTrue(Effector(agent.internal["SELF.PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertFalse(Effector(agent.internal["SELF.MENTAL-EFFECTOR.1"]).is_free())

        # 3a) Assess
        agent.iidea()

        # 3b) There is one instance of ACKNOWLEDGE-LANGUAGE-INPUT; it is satisfied
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-LANGUAGE-INPUT", status=Goal.Status.SATISFIED)

        # 3c) There is one decision, for ACKNOWLEDGE-LANGUAGE-INPUT > acknowledge language input > Step 1; it is finished
        self.assertEqual(1, len(agent.decisions()))
        self.assertDecisionExists(agent, status=Decision.Status.FINISHED, goal="SELF.GOAL.1", plan="SELF.PLAN.1", step="SELF.STEP.1", outputs=["OUTPUTS.XMR.1"])

        # 3d) There is one instance of BUILD-A-CHAIR; it is pending
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.PENDING)

        # 3e) Both effectors are free
        self.assertTrue(Effector(agent.internal["SELF.PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertTrue(Effector(agent.internal["SELF.MENTAL-EFFECTOR.1"]).is_free())

        # 4a) Decide
        agent.iidea()

        # 4b) There is one instance of BUILD-A-CHAIR; it is active
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE)

        # 4c) There is one incomplete decision, for BUILD-A-CHAIR > as-taught-by-jake > Step 1; it is selected, and has an output, no effectors, and no callbacks
        self.assertEqual(2, len(agent.decisions()))
        self.assertDecisionExists(agent, status=Decision.Status.SELECTED, goal="SELF.GOAL.2", plan="SELF.PLAN.2", step="SELF.STEP.2", outputs=["OUTPUTS.XMR.2"], effectors=[], callbacks=[])

        # 5a) Execute
        agent.iidea()

        # 5b) There is one instance of BUILD-A-CHAIR; it is active
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE)

        # 5c) There is one incomplete decision, for BUILD-A-CHAIR > as-taught-by-jake > Step 1; it is executing, and has an output, an effector, and a callback
        self.assertEqual(2, len(agent.decisions()))
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="SELF.GOAL.2", plan="SELF.PLAN.2", step="SELF.STEP.2", outputs=["OUTPUTS.XMR.2"], effectors=["SELF.PHYSICAL-EFFECTOR.1"], callbacks=["SELF.CALLBACK.2"])

        # 5d) The decision's callback is waiting
        self.assertEqual(Callback.Status.WAITING, agent.decisions()[1].callbacks()[0].status())

        # 5e) The physical effector is reserved; the mental effector is free
        self.assertFalse(Effector(agent.internal["SELF.PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertTrue(Effector(agent.internal["SELF.MENTAL-EFFECTOR.1"]).is_free())

        # 6a) Assess
        agent.iidea()

        # 6b) The state has not changed; repeat all tests from #5
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE)
        self.assertEqual(2, len(agent.decisions()))
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="SELF.GOAL.2", plan="SELF.PLAN.2", step="SELF.STEP.2", outputs=["OUTPUTS.XMR.2"], effectors=["SELF.PHYSICAL-EFFECTOR.1"], callbacks=["SELF.CALLBACK.2"])
        self.assertEqual(Callback.Status.WAITING, agent.decisions()[1].callbacks()[0].status())
        self.assertFalse(Effector(agent.internal["SELF.PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertTrue(Effector(agent.internal["SELF.MENTAL-EFFECTOR.1"]).is_free())

        # 7a) Advance time several iterations
        agent.iidea()  # Decide
        agent.iidea()  # Execute
        agent.iidea()  # Assess
        agent.iidea()  # Decide
        agent.iidea()  # Execute
        agent.iidea()  # Assess
        agent.iidea()  # Decide
        agent.iidea()  # Execute

        # 7b) The state has not changed; repeat all tests from #5
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE)
        self.assertEqual(2, len(agent.decisions()))
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="SELF.GOAL.2", plan="SELF.PLAN.2", step="SELF.STEP.2", outputs=["OUTPUTS.XMR.2"], effectors=["SELF.PHYSICAL-EFFECTOR.1"], callbacks=["SELF.CALLBACK.2"])
        self.assertEqual(Callback.Status.WAITING, agent.decisions()[1].callbacks()[0].status())
        self.assertFalse(Effector(agent.internal["SELF.PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertTrue(Effector(agent.internal["SELF.MENTAL-EFFECTOR.1"]).is_free())

        # 7c) Issue the callback
        agent.callback("SELF.CALLBACK.2")

        # 7d) The decision's callback is received
        self.assertEqual(Callback.Status.RECEIVED, agent.decisions()[1].callbacks()[0].status())

        # 7e) The goal is still marked as active
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE)

        # 8a) Assess
        agent.iidea()

        # 8a) The goal is now satisfied
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.SATISFIED)

        # 8b) There are no executing decisions
        self.assertEqual(2, len(agent.decisions()))
        self.assertEqual(2, len(list(filter(lambda decision: decision.status() != Decision.Status.EXECUTING, agent.decisions()))))

        # 8c) The effectors are free
        self.assertTrue(Effector(agent.internal["SELF.PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertTrue(Effector(agent.internal["SELF.MENTAL-EFFECTOR.1"]).is_free())