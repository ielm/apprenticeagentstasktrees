from backend.agent import Agent
from backend.models.agenda import Decision, Goal
from ontograph.Frame import Frame
# from backend.models.bootstrap import Bootstrap
# from backend.models.effectors import Callback, Effector
# from backend.models.ontology import Ontology

from tests.experiments.ExperimentTestCase import ExperimentTestCase


class ImpassesExperimentTestCase(ExperimentTestCase):

    def test_example_throughput(self):

        agent = Agent()

        # Bootstrap the knowledge
        agent.load_knowledge("backend.resources.example", "impasses.knowledge")

        # The agenda is empty
        self.assertEqual(0, len(agent.agenda().goals()))
        self.assertEqual(0, len(agent.decisions()))

        # 1a) Any TMR input to trigger the first goal.
        agent._input(self.analyses()[0])

        # 1b) IIDEA loop
        self.iidea_loop(agent)

        # 1c) TEST: GOAL-THAT-WILL-BE-BLOCKED is active
        #     TEST: SOME-SUBGOAL is pending
        #     TEST: 1 Decision: GOAL-THAT-WILL-BE-BLOCKED > plan that will be blocked > Step 1 == BLOCKED
        #           with impasse EXE.SOME-SUBGOAL.1
        self.assertGoalExists(agent, isa="@EXE.GOAL-THAT-WILL-BE-BLOCKED", status=Goal.Status.ACTIVE)
        self.assertGoalExists(agent, isa="@EXE.SOME-SUBGOAL", status=Goal.Status.PENDING)
        self.assertDecisionExists(agent, status=Decision.Status.BLOCKED, goal="@SELF.GOAL.1", plan="@SELF.PLAN.1", step="@SELF.STEP.1", impasses=["@EXE.SOME-SUBGOAL.1"])

        # 2a) IIDEA loop
        self.iidea_loop(agent)

        # 1c) TEST: GOAL-THAT-WILL-BE-BLOCKED is active
        #     TEST: SOME-SUBGOAL is active
        #     TEST: Decision GOAL-THAT-WILL-BE-BLOCKED > plan that will be blocked > Step 1 == BLOCKED
        #           with impasse EXE.SOME-SUBGOAL.1
        #     TEST: Decision SOME-SUBGOAL > get around an impasse > Step 1 == EXECUTING
        #           with callback SELF.CALLBACK.1
        self.assertGoalExists(agent, isa="@EXE.GOAL-THAT-WILL-BE-BLOCKED", status=Goal.Status.ACTIVE)
        self.assertGoalExists(agent, isa="@EXE.SOME-SUBGOAL", status=Goal.Status.ACTIVE)
        self.assertDecisionExists(agent, status=Decision.Status.BLOCKED, goal="@SELF.GOAL.1", plan="@SELF.PLAN.1", step="@SELF.STEP.1", impasses=["@EXE.SOME-SUBGOAL.1"])
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="@EXE.SOME-SUBGOAL.1", plan="@EXE.PLAN.2", step="@EXE.STEP.2", callbacks=["@SELF.CALLBACK.1"])

        # 3a) Callback
        agent.callback("SELF.CALLBACK.1")

        # 3b) IIDEA loop
        self.iidea_loop(agent)

        # 3c) TEST: GOAL-THAT-WILL-BE-BLOCKED is active
        #     TEST: SOME-SUBGOAL is satisfied
        #     TEST: Decision GOAL-THAT-WILL-BE-BLOCKED > plan that will be blocked > Step 1 == PENDING
        #           with no impasses
        #     TEST: Decision SOME-SUBGOAL > get around an impasse > Step 1 == FINISHED
        #           with no callbacks
        self.assertGoalExists(agent, isa="@EXE.GOAL-THAT-WILL-BE-BLOCKED", status=Goal.Status.ACTIVE)
        self.assertGoalExists(agent, isa="@EXE.SOME-SUBGOAL", status=Goal.Status.SATISFIED)
        self.assertDecisionExists(agent, status=Decision.Status.PENDING, goal="@SELF.GOAL.1", plan="@SELF.PLAN.1", step="@SELF.STEP.1", impasses=[])
        self.assertDecisionExists(agent, status=Decision.Status.FINISHED, goal="@EXE.SOME-SUBGOAL.1", plan="@EXE.PLAN.2", step="@EXE.STEP.2", callbacks=[])

        # 4a) IIDEA loop
        self.iidea_loop(agent)

        # 4b) TEST: GOAL-THAT-WILL-BE-BLOCKED is active
        #     TEST: SOME-SUBGOAL is satisfied
        #     TEST: Decision GOAL-THAT-WILL-BE-BLOCKED > plan that will be blocked > Step 1 == EXECUTING
        #           with callback SELF.CALLBACK.2
        self.assertGoalExists(agent, isa="@EXE.GOAL-THAT-WILL-BE-BLOCKED", status=Goal.Status.ACTIVE)
        self.assertGoalExists(agent, isa="@EXE.SOME-SUBGOAL", status=Goal.Status.SATISFIED)
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="@SELF.GOAL.1", plan="@SELF.PLAN.1", step="@SELF.STEP.1", callbacks=["@SELF.CALLBACK.2"])

        # 5a) Callback
        agent.callback("@SELF.CALLBACK.2")

        # 5b) IIDEA loop
        self.iidea_loop(agent)

        # 4b) TEST: GOAL-THAT-WILL-BE-BLOCKED is satisfied
        #     TEST: SOME-SUBGOAL is satisfied
        #     TEST: Decision GOAL-THAT-WILL-BE-BLOCKED > plan that will be blocked > Step 1 == FINISHED
        #           with no callbacks
        self.assertGoalExists(agent, isa="@EXE.GOAL-THAT-WILL-BE-BLOCKED", status=Goal.Status.SATISFIED)
        self.assertGoalExists(agent, isa="@EXE.SOME-SUBGOAL", status=Goal.Status.SATISFIED)
        self.assertDecisionExists(agent, status=Decision.Status.FINISHED, goal="@SELF.GOAL.1", plan="@SELF.PLAN.1", step="@SELF.STEP.1", callbacks=[])
