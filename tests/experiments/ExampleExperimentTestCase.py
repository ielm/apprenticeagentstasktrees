from backend.agent import Agent
from backend.models.agenda import Decision, Goal
from backend.models.bootstrap import Bootstrap
from backend.models.effectors import Callback, Effector
from backend.utils.OntologyLoader import OntologyServiceLoader

from tests.experiments.ExperimentTestCase import ExperimentTestCase


class ExampleExperimentTestCase(ExperimentTestCase):

    def test_example_throughput(self):

        OntologyServiceLoader().load()
        agent = Agent()

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
        self.assertGoalExists(agent, isa="@EXE.ACKNOWLEDGE-LANGUAGE-INPUT", status=Goal.Status.ACTIVE, query=lambda goal: goal.resolve("$tmr")._identifier == "@INPUTS.XMR.1")

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