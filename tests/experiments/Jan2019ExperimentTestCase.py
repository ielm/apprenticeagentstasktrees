from backend.agent import Agent
from backend.models.agenda import Decision, Goal, Step
from backend.models.bootstrap import Bootstrap
from backend.models.effectors import Effector
from backend.models.ontology import Ontology
from backend.models.xmr import XMR
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

    def test_1_1(self):

        agent = Agent(ontology=Ontology.init_default())

        #######

        # Pa) Load LTM with the chair building instructions
        Bootstrap.bootstrap_resource(agent, "backend.resources.experiments", "chair.knowledge")

        # Pb) There is an instance of "Jake", who is known, present, and taught the robot the chair instructions
        Bootstrap.bootstrap_resource(agent, "backend.resources.experiments", "Jan2019_1_1.environment")
        Bootstrap.bootstrap_resource(agent, "backend.resources.experiments", "Jan2019_1_1.knowledge")

        #######

        # 1a) Input from "Jake", "Let's build a chair."
        agent._input(self.analyses()[0], source="LT.HUMAN.1")

        # 1b) IIDEA loop
        self.iidea_loop(agent)

        # 1c) TEST: An instance of ACKNOWLEDGE-LANGUAGE-INPUT with the correct TMR was triggered, and executed
        #     TEST: An instance of BUILD-A-CHAIR is pending
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-LANGUAGE-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: goal.resolve("$tmr")["REFERS-TO-GRAPH"].singleton() == "TMR#1")
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.PENDING)

        # 1d) IIDEA loop
        self.iidea_loop(agent)

        # 1e) TEST: An instance of BUILD-A-CHAIR is in progress, with the first step waiting on the physical effector
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["FETCH-OBJECT-CAPABILITY"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.2"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["SCREWDRIVER.1"], XMR(agent.outputs["XMR.2"]).graph(agent)["FETCH.1"]["THEME"].singleton())

        #######

        # 2a) Visual input "Jake leaves"
        agent._input(self.observations()["Jake leaves"], type=XMR.Type.VISUAL.name)

        # 2b) TEST: Jake is no longer in the environment
        with self.assertRaises(Exception):
            agent.env().location("ENV.HUMAN.1")

        # 2c) IIDEA loop
        self.iidea_loop(agent)

        # 2d) TEST: An instance of BUILD-A-CHAIR is in progress, with the first step waiting on the physical effector
        #     TEST: An instance of ACKNOWLEDGE-VISUAL-INPUT with the correct VMR was triggered, and executed (no effect)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#1"])
        self.assertFalse(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertTrue(Effector(agent.internal["MENTAL-EFFECTOR.1"]).is_free())
        self.assertTrue(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())

        #######

        # 3a) Callback input capability GET(screwdriver) is complete
        agent.callback("SELF.CALLBACK.2")

        # 3b) Visual input "the screwdriver has been moved"
        agent._input(self.observations()["Screwdriver location changes to workspace"], type=XMR.Type.VISUAL.name)

        # 3c) TEST: The screwdriver is "close" to the agent
        self.assertEqual(agent.environment["WORKSPACE.1"], agent.env().location("ENV.SCREWDRIVER.1"))

        # 3d) IIDEA loop
        self.iidea_loop(agent)

        # 3e) TEST: An instance of BUILD-A-CHAIR is in progress, with the first step finished
        #     TEST: An instance of ACKNOWLEDGE-VISUAL-INPUT with the correct VMR was triggered, and executed (no effect)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#2"])

        # 3f) IIDEA loop
        self.iidea_loop(agent)

        # 3g) TEST: An instance of BUILD-A-CHAIR is in progress, with the second step waiting on the physical effector
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["FETCH-OBJECT-CAPABILITY"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.3"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["BRACKET.1"], XMR(agent.outputs["XMR.3"]).graph(agent)["FETCH.1"]["THEME"].singleton())

        #######

        # 4a) Visual input "Jake returns"
        agent._input(self.observations()["Jake enters"], type=XMR.Type.VISUAL.name)

        # 4b) TEST: Jake is in the environment
        self.assertEqual(agent.ontology["LOCATION"], agent.env().location("ENV.HUMAN.1"))

        # 4c) IIDEA loop
        self.iidea_loop(agent)

        # 4d) TEST: An instance of ACKNOWLEDGE-VISUAL-INPUT with the correct VMR was triggered, and executed
        #     TEST: An instance of GREET-AGENT with the correct VMR was created
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#3"])
        self.assertGoalExists(agent, isa="EXE.GREET-HUMAN", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$human") == agent.environment["HUMAN.1"])

        # 4e) IIDEA loop
        self.iidea_loop(agent)

        # 4f) An instance of GREET-AGENT is in progress, with the first step waiting on the verbal effector
        self.assertGoalExists(agent, isa="EXE.GREET-HUMAN", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["SPEAK-CAPABILITY"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.5"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["HUMAN.1"], XMR(agent.outputs["XMR.5"]).graph(agent)["GREET.1"]["THEME"].singleton())

        #######

        # 5a) Callback input capability SPEAK("Hi Jake.") is complete
        agent.callback("SELF.CALLBACK.5")

        # 5b) IIDEA loop
        self.iidea_loop(agent)

        # 5c) TEST: GREET-HUMAN is "satisfied"
        self.assertGoalExists(agent, isa="EXE.GREET-HUMAN", status=Goal.Status.SATISFIED, query=lambda goal: goal.resolve("$human") == agent.environment["HUMAN.1"])
        self.assertTrue(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())

        # 5d) TEST: BUILD-A-CHAIR is still "active"
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)

        #######

        # 6a) Input from "Jake", "What are you doing?"
        agent._input(self.analyses()[1], source="LT.HUMAN.1")

        # 6b) IIDEA loop
        self.iidea_loop(agent)

        # 6c) TEST: An instance of ACKNOWLEDGE-LANGUAGE-INPUT with the correct TMR was triggered and executed
        #     TEST: An instance of RESPOND-TO-QUERY with the correct TMR is pending on the agenda
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-LANGUAGE-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: goal.resolve("$tmr")["REFERS-TO-GRAPH"].singleton() == "TMR#2")
        self.assertGoalExists(agent, isa="EXE.RESPOND-TO-QUERY", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$tmr")["REFERS-TO-GRAPH"].singleton() == "TMR#2")

        # 6d) TEST: BUILD-A-CHAIR is still "active"
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)

        # 6e) IIDEA loop
        self.iidea_loop(agent)

        # 6f) TEST: An instance of RESPOND-TO-QUERY is running, with an output XMR with the correct verbal response
        self.assertGoalExists(agent, isa="EXE.RESPOND-TO-QUERY", status=Goal.Status.ACTIVE, query=lambda goal: goal.resolve("$tmr")["REFERS-TO-GRAPH"].singleton() == "TMR#2")
        self.assertFalse(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["SPEAK-CAPABILITY"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.7"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent["XMR#3"]["FETCH.1"], XMR(agent.outputs["XMR.7"]).graph(agent)["DESCRIBE.1"]["THEME"].singleton())

        # 6g) TEST: BUILD-A-CHAIR is still "active"
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)

        #######

        # 7a) Callback input capability SPEAK("I am fetching a foot bracket.") is complete
        agent.callback("SELF.CALLBACK.7")

        # 7b) IIDEA loop
        self.iidea_loop(agent)

        # 7c) TEST: RESPOND-TO-QUERY is "satisfied"
        self.assertGoalExists(agent, isa="EXE.RESPOND-TO-QUERY", status=Goal.Status.SATISFIED, query=lambda goal: goal.resolve("$tmr")["REFERS-TO-GRAPH"].singleton() == "TMR#2")
        self.assertTrue(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())

        # 7d) TEST: BUILD-A-CHAIR is still "active"
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)

        #######

        # 8a) Callback input capability GET(foot_bracket)
        agent.callback("SELF.CALLBACK.3")

        # 8b) IIDEA loop
        self.iidea_loop(agent)

        # 8c) TEST: An instance of BUILD-A-CHAIR is in progress, with the second step finished
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[2].status() == Step.Status.PENDING)

        # 8d) IIDEA loop
        self.iidea_loop(agent)

        # 8e) TEST: An instance of BUILD-A-CHAIR is in progress, with the third step waiting on the physical effector
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[2].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["FETCH-OBJECT-CAPABILITY"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.8"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["BRACKET.2"], XMR(agent.outputs["XMR.8"]).graph(agent)["FETCH.1"]["THEME"].singleton())

    def test_1_2(self):

        agent = Agent(ontology=Ontology.init_default())

        #######

        # Pa) Load LTM with the chair building instructions
        Bootstrap.bootstrap_resource(agent, "backend.resources.experiments", "chair.knowledge")

        # Pb) There is an instance of "Jake", who is known, present, and taught the robot the chair instructions
        Bootstrap.bootstrap_resource(agent, "backend.resources.experiments", "Jan2019_1_2.environment")
        Bootstrap.bootstrap_resource(agent, "backend.resources.experiments", "Jan2019_1_2.knowledge")

        #######

        # 1a) Input from "Jake", "Let's build a chair."
        agent._input(self.analyses()[0], source="LT.HUMAN.1")

        # 1b) IIDEA loop
        self.iidea_loop(agent)

        # 1c) TEST: An instance of ACKNOWLEDGE-LANGUAGE-INPUT with the correct TMR was triggered, and executed
        #     TEST: An instance of BUILD-A-CHAIR is pending
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-LANGUAGE-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: goal.resolve("$tmr")["REFERS-TO-GRAPH"].singleton() == "TMR#1")
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.PENDING)

        # 1d) IIDEA loop
        self.iidea_loop(agent)

        # 1e) TEST: An instance of BUILD-A-CHAIR is in progress, with the first step waiting on the physical effector
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["FETCH-OBJECT-CAPABILITY"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.2"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["SCREWDRIVER.1"], XMR(agent.outputs["XMR.2"]).graph(agent)["FETCH.1"]["THEME"].singleton())

        #######

        # 2a) Visual input "Jake leaves"
        agent._input(self.observations()["Jake leaves"], type=XMR.Type.VISUAL.name)

        # 2b) TEST: Jake is no longer in the environment
        with self.assertRaises(Exception):
            agent.env().location("ENV.HUMAN.1")

        # 2c) IIDEA loop
        self.iidea_loop(agent)

        # 2d) TEST: An instance of BUILD-A-CHAIR is in progress, with the first step waiting on the physical effector
        #     TEST: An instance of ACKNOWLEDGE-VISUAL-INPUT with the correct VMR was triggered, and executed (no effect)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#1"])
        self.assertFalse(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertTrue(Effector(agent.internal["MENTAL-EFFECTOR.1"]).is_free())
        self.assertTrue(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())

        #######

        # 3a) Callback input capability GET(screwdriver) is complete
        agent.callback("SELF.CALLBACK.2")

        # 3b) Visual input "the screwdriver has been moved"
        agent._input(self.observations()["Screwdriver location changes to workspace"], type=XMR.Type.VISUAL.name)

        # 3c) TEST: The screwdriver is "close" to the agent
        self.assertEqual(agent.environment["WORKSPACE.1"], agent.env().location("ENV.SCREWDRIVER.1"))

        # 3d) IIDEA loop
        self.iidea_loop(agent)

        # 3e) TEST: An instance of BUILD-A-CHAIR is in progress, with the first step finished
        #     TEST: An instance of ACKNOWLEDGE-VISUAL-INPUT with the correct VMR was triggered, and executed (no effect)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#2"])

        # 3f) IIDEA loop
        self.iidea_loop(agent)

        # 3g) TEST: An instance of BUILD-A-CHAIR is in progress, with the second step waiting on the physical effector
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["FETCH-OBJECT-CAPABILITY"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.3"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["BRACKET.1"], XMR(agent.outputs["XMR.3"]).graph(agent)["FETCH.1"]["THEME"].singleton())

        #######

        # 4a) Callback input capability GET(bracket) is complete
        agent.callback("SELF.CALLBACK.3")

        # 4b) IIDEA loop
        self.iidea_loop(agent)

        # 4c) TEST: An instance of BUILD-A-CHAIR is in progress, with the second step finished
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[2].status() == Step.Status.PENDING)

        # 4d) IIDEA loop
        self.iidea_loop(agent)

        # 4e) TEST: An instance of BUILD-A-CHAIR is in progress, with the third step waiting on the physical effector
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[2].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["FETCH-OBJECT-CAPABILITY"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.4"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["DOWEL.1"], XMR(agent.outputs["XMR.4"]).graph(agent)["FETCH.1"]["THEME"].singleton())

        #######

        # 5a) Callback input capability GET(dowel) is complete
        agent.callback("SELF.CALLBACK.4")

        # 5b) IIDEA loop
        self.iidea_loop(agent)

        # 5c) TEST: An instance of BUILD-A-CHAIR is in progress, with the third step finished
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[2].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[3].status() == Step.Status.PENDING)

        # 5d) IIDEA loop
        self.iidea_loop(agent)

        # 5e) TEST: An instance of BUILD-A-CHAIR is in progress, with the fourth step is pending, blocked on REQUEST-HELP
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[3].status() == Step.Status.PENDING)
        self.assertGoalExists(agent, isa="EXE.REQUEST-HELP", status=Goal.Status.PENDING)
        self.assertDecisionExists(agent, status=Decision.Status.BLOCKED, goal="SELF.GOAL.2", impasses=["SELF.REQUEST-HELP.1"])

        # 5f) IIDEA loop
        self.iidea_loop(agent)

        # 5g) TEST: An instance of BUILD-A-CHAIR is in progress, with the fourth step is pending, blocked on REQUEST-HELP
        #     TEST: An instance of REQUEST-HELP is in progress, waiting on SPEAK-CAPABILITY
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[3].status() == Step.Status.PENDING)
        self.assertGoalExists(agent, isa="EXE.REQUEST-HELP", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["SPEAK-CAPABILITY"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.5"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_output())
        self.assertEqual(XMR(agent.outputs["XMR.5"]).graph(agent)["ATTACH.1"], XMR(agent.outputs["XMR.5"]).graph(agent)["REQUEST-ACTION.1"]["PURPOSE"].singleton())
        self.assertDecisionExists(agent, status=Decision.Status.BLOCKED, goal="SELF.GOAL.2", impasses=["SELF.REQUEST-HELP.1"])

        #######

        # 6a) Callback input capability SPEAK("Jake, come back, you need to screw the bracket to the dowel.") is complete
        agent.callback("SELF.CALLBACK.5")

        # 6b) IIDEA loop
        self.iidea_loop(agent)

        # 6c) TEST: An instance of BUILD-A-CHAIR is in progress, with the fourth step finished
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[2].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[3].status() == Step.Status.PENDING)

        # 6d) TEST: The verbal effector is released; the decision is still blocked
        self.assertTrue(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())
        self.assertDecisionExists(agent, status=Decision.Status.BLOCKED, goal="SELF.GOAL.2", impasses=["SELF.REQUEST-HELP.1"])

        #######

        # 7a) Visual input "Jake returns"
        agent._input(self.observations()["Jake enters"], type=XMR.Type.VISUAL.name)

        # 7b) TEST: Jake is in the environment
        self.assertEqual(agent.ontology["LOCATION"], agent.env().location("ENV.HUMAN.1"))

        # 7c) IIDEA loop
        self.iidea_loop(agent)

        # 7d) TEST: An instance of ACKNOWLEDGE-VISUAL-INPUT with the correct VMR was triggered, and executed
        #     TEST: An instance of GREET-AGENT with the correct VMR was created
        #     TEST: An instance of SELF.REQUEST-HELP was satisfied
        #     TEST: An instance of BUILD-A-CHAIR is no longer blocked
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#3"])
        self.assertGoalExists(agent, isa="EXE.GREET-HUMAN", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$human") == agent.environment["HUMAN.1"])
        self.assertGoalExists(agent, isa="EXE.REQUEST-HELP", status=Goal.Status.SATISFIED)
        self.assertDecisionExists(agent, status=Decision.Status.PENDING, goal="SELF.GOAL.2", impasses=[])

        # 7e) IIDEA loop
        self.iidea_loop(agent)

        # 7f) An instance of GREET-AGENT is in progress, with the first step waiting on the verbal effector
        self.assertGoalExists(agent, isa="EXE.GREET-HUMAN", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["SPEAK-CAPABILITY"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.outputs["XMR.7"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["HUMAN.1"], XMR(agent.outputs["XMR.7"]).graph(agent)["GREET.1"]["THEME"].singleton())

        #######

        # 8a) Callback input capability SPEAK("Hi Jake.") is complete
        agent.callback("SELF.CALLBACK.7")

        # 8b) IIDEA loop
        self.iidea_loop(agent)

        # 8c) TEST: GREET-HUMAN is "satisfied"
        self.assertGoalExists(agent, isa="EXE.GREET-HUMAN", status=Goal.Status.SATISFIED, query=lambda goal: goal.resolve("$human") == agent.environment["HUMAN.1"])
        self.assertTrue(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())

        # 8d) TEST: An instance of BUILD-A-CHAIR is in progress, with the fourth step finished
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[2].status() == Step.Status.FINISHED)
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[3].status() == Step.Status.PENDING)
        self.assertDecisionExists(agent, status=Decision.Status.EXECUTING, goal="SELF.GOAL.2", impasses=[])

        #######

        # 9a) Visual input "Jake affixes the bracket to the dowel with the screwdriver"
        agent._input(self.observations()["Jake affixes the bracket to the dowel with the screwdriver"], type=XMR.Type.VISUAL.name)

        # 9b) IIDEA loop
        self.iidea_loop(agent)

        # 9c) TEST: An instance of BUILD-A-CHAIR is satisfied
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.SATISFIED)