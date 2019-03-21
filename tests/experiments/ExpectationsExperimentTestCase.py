from backend.Agent import Agent
from backend.models.agenda import Decision, Goal
# from backend.models.bootstrap import Bootstrap
# from backend.models.ontology import Ontology
from ontograph import graph

from tests.experiments.ExperimentTestCase import ExperimentTestCase


class ExpectationsExperimentTestCase(ExperimentTestCase):

    def test_example_throughput(self):

        graph.reset()
        agent = Agent()

        # Bootstrap the knowledge
        agent.load_knowledge("backend.resources.example", "expectations.knowledge")

        # The agenda is empty
        self.assertEqual(0, len(agent.agenda().goals()))
        self.assertEqual(0, len(agent.decisions()))

        # 1a) Any TMR input to trigger the first goal.
        agent._input(self.analyses()[0])

        # 1b) IIDEA loop
        self.iidea_loop(agent)

        # 1c) TEST: GOAL-WITH-EXPECTATION is active
        #     TEST: 1 Decision: GOAL-WITH-EXPECTATION > plan with expectation > Step 1 == EXECUTING
        #           with expectation SELF.EXPECTATION.1
        self.assertGoalExists(agent, isa="@EXE.GOAL-WITH-EXPECTATION", status=Goal.Status.ACTIVE)
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="@SELF.GOAL.1", plan="@SELF.PLAN.1", step="@SELF.STEP.1", expectations=["@SELF.EXPECTATION.1"])

        # 2a) Adjust memory to include an instance of a PHYSICAL-EVENT with AGENT = the human and THEME = the screwdriver
        graph.ontolang().run('''
            @WM.PHYSICAL-EVENT.1 = {
                IS-A @ONT.PHYSICAL-EVENT;
                AGENT @ENV.HUMAN.1;
                THEME @ENV.SCREWDRIVER.1;
            };
        ''')

        # 2b) IIDEA loop
        self.iidea_loop(agent)

        # 2c) TEST: GOAL-WITH-EXPECTATION is active
        #     TEST: Decision: GOAL-WITH-EXPECTATION > plan with expectation > Step 1 == FINISHED
        #           with expectation SELF.EXPECTATION.1
        self.assertGoalExists(agent, isa="@EXE.GOAL-WITH-EXPECTATION", status=Goal.Status.ACTIVE)
        self.assertDecisionExists(agent, status=Decision.Status.FINISHED, goal="@SELF.GOAL.1", plan="@SELF.PLAN.1", step="@SELF.STEP.1", expectations=["@SELF.EXPECTATION.1"])

        # 3a) IIDEA loop
        self.iidea_loop(agent)

        # 3b) TEST: GOAL-WITH-EXPECTATION is active
        #     TEST: Decision: GOAL-WITH-EXPECTATION > plan with expectation > Step 2 == EXECUTING
        #           with callback SELF.CALLBACK.1
        self.assertGoalExists(agent, isa="@EXE.GOAL-WITH-EXPECTATION", status=Goal.Status.ACTIVE)
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="@SELF.GOAL.1", plan="@SELF.PLAN.1", step="@SELF.STEP.2", callbacks=["@SELF.CALLBACK.1"])

        # 4a) Callback
        agent.callback("@SELF.CALLBACK.1")

        # 4b) IIDEA loop
        self.iidea_loop(agent)

        # 3b) TEST: GOAL-WITH-EXPECTATION is satisfied
        #     TEST: Decision: GOAL-WITH-EXPECTATION > plan with expectation > Step 2 == FINISHED
        #           with no callbacks
        self.assertGoalExists(agent, isa="@EXE.GOAL-WITH-EXPECTATION", status=Goal.Status.SATISFIED)
        self.assertDecisionExists(agent, status=Decision.Status.FINISHED, goal="@SELF.GOAL.1", plan="@SELF.PLAN.1", step="@SELF.STEP.2", callbacks=[])
