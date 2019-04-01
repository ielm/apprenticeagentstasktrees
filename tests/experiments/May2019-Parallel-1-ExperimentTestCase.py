from backend import agent
from backend.models.agenda import Decision, Goal, Step
from backend.models.effectors import Effector
from backend.models.xmr import XMR
from backend.utils.OntologyLoader import OntologyServiceLoader
from ontograph.Frame import Frame
from tests.experiments.ExperimentTestCase import ExperimentTestCase

from pkgutil import get_data

import json


class Jan2019Experiment(ExperimentTestCase):

    @staticmethod
    def analyses():
        return json.loads(get_data("tests.resources", "DemoJan2019_Analyses.json").decode('ascii'))

    @staticmethod
    def observations():
        return json.loads(get_data("tests.resources", "DemoJan2019_Observations_VMR.json").decode('ascii'))

    def test_robot_1(self):

        agent.reset()
        OntologyServiceLoader().load()

        #######

        # Pa) There is an instance of "Jake", who is known, present, and taught the robot the chair instructions
        agent.load_knowledge("backend.resources.experiments", "Parallel_1.environment")
        agent.load_knowledge("backend.resources.experiments", "Parallel_1.knowledge")

        #######

        # 1a) There is an instance of the goal @ONT.BUILD-A-CHAIR on the agenda, pending
        self.assertGoalExists(agent, isa="@ONT.BUILD-A-CHAIR", status=Goal.Status.PENDING)

        # 1b) The human is not in the field of view
        with self.assertRaises(Exception):
            agent.env().location("@ENV.HUMAN.1")

        #######

        # 2a) IIDEA loop
        self.iidea_loop(agent)

        # 2b) The instance of @ONT.BUILD-A-CHAIR is active, and the first step of the only plan is pending
        self.assertGoalExists(agent, isa="@ONT.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)

        # 2c) The physical effector is reserved, pending a callback
        self.assertFalse(Effector(Frame("@SELF.EFFECTOR.1")).is_free())
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="@SELF.GOAL.1", outputs=["@OUTPUTS.XMR.1"], callbacks=["@SELF.CALLBACK.1"])

        # 2d) The physical output is "I am taking the TRANSFER-OBJECT(@ENV.SCREWDRIVER.1) action."
        self.assertEqual("I am taking the TRANSFER-OBJECT(@ENV.SCREWDRIVER.1) action.", XMR.from_instance(Frame("@OUTPUTS.XMR.1")).render())

        #######

        # 3a) The human enters the field of view
        agent._input(self.observations()["Jake enters"], type=XMR.Type.VISUAL.name)

        # 3b) The human is in the field of view
        self.assertEqual("@ONT.LOCATION", agent.env().location("@ENV.HUMAN.1"))

        # 3c) IIDEA loop
        self.iidea_loop(agent)

        # 3d) The instance of @ONT.BUILD-A-CHAIR is active, and the first step of the only plan is pending
        self.assertGoalExists(agent, isa="@ONT.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)

        # 3e) There is a pending instance of @ONT.GREET-HUMAN
        self.assertGoalExists(agent, isa="@ONT.GREET-HUMAN", status=Goal.Status.PENDING)

        # 3f) IIDEA loop
        self.iidea_loop(agent)

        # 3g) There is an instance of @ONT.GREET-HUMAN, and the first step of the only plan is pending
        self.assertGoalExists(agent, isa="@ONT.GREET-HUMAN", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)

        # 3h) The verbal effector is reserved, pending a callback
        self.assertFalse(Effector(Frame("@SELF.EFFECTOR.2")).is_free())
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="@SELF.GOAL.3", outputs=["@OUTPUTS.XMR.2"], callbacks=["@SELF.CALLBACK.2"])

        # 3i) The verbal output is "Hi Jake."
        self.assertEqual("Hi Jake.", XMR.from_instance(Frame("@OUTPUTS.XMR.2")).render())

        #######

        # 4a) Callback the verbal output
        agent.callback("@SELF.CALLBACK.2")

        # 4b) IIDEA loop
        self.iidea_loop(agent)

        # 4c) The instance of @ONT.GREET-HUMAN is satisfied
        self.assertGoalExists(agent, isa="@ONT.GREET-HUMAN", status=Goal.Status.SATISFIED)

        #######

        # 4a) Callback the physical output
        agent.callback("@SELF.CALLBACK.1")

        # 4b) IIDEA loop
        self.iidea_loop(agent)

        # 4c) The instance of @ONT.BUILD-A-CHAIR is active, and the first step of the only plan is complete; the second step is active
        self.assertGoalExists(agent, isa="@ONT.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="@ONT.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)

