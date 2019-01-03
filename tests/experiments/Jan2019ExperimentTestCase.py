from backend.agent import Agent
from backend.models.agenda import Goal, Step
from backend.models.bootstrap import Bootstrap
from backend.models.effectors import Capability, Effector
from backend.models.graph import Frame, Identifier
from backend.models.mps import AgentMethod
from backend.models.ontology import Ontology
from backend.models.output import OutputXMR
from backend.models.xmr import XMR

from pkgutil import get_data
from typing import Callable, Type, Union
from unittest.mock import patch

import json
import unittest

from backend.resources.experiments.Jan2019_1_1 import GetPhysicalObjectCapabilityMP, SpeakCapabilityMP


class Jan2019Experiment(unittest.TestCase):

    def setUp(self):
        from backend.models.tmr import TMR
        from backend.utils.AtomicCounter import AtomicCounter

        TMR.counter = AtomicCounter()

    @staticmethod
    def analyses():
        return json.loads(get_data("tests.resources", "DemoJan2019_Analyses.json").decode('ascii'))

    @staticmethod
    def observations():
        return json.loads(get_data("tests.resources", "DemoJan2019_Observations_VMR.json").decode('ascii'))

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

    def assertEffectorReserved(self, agent: Agent, effector: Union[str, Identifier, Frame, Effector], goal: [str, Identifier, Frame, Goal], capability: Union[str, Identifier, Frame, Capability]):

        if isinstance(effector, str):
            effector = Identifier.parse(effector)
        if isinstance(effector, Identifier):
            effector = agent.lookup(effector)
        if isinstance(effector, Frame):
            effector = Effector(effector)

        if isinstance(goal, str):
            goal = Identifier.parse(goal)
        if isinstance(goal, Identifier):
            goal = agent.lookup(goal)
        if isinstance(goal, Frame):
            goal = Goal(goal)

        if isinstance(capability, str):
            capability = Identifier.parse(capability)
        if isinstance(capability, Identifier):
            capability = agent.lookup(capability)
        if isinstance(capability, Frame):
            capability = Capability(capability)

        self.assertFalse(effector.is_free())
        self.assertEqual(goal, effector.effecting())
        self.assertTrue(effector.frame["USES"] == capability.frame)

    def test_1_1(self):

        agent = Agent(ontology=Ontology.init_default())

        #######

        # Pa) Load LTM with the chair building instructions
        Bootstrap.bootstrap_resource(agent, "backend.resources.experiments", "chair.knowledge")

        # Pb) There is an instance of "Jake", who is known, present, and taught the robot the chair instructions
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
        self.assertEqual(agent.internal["XMR.3"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["SCREWDRIVER.1"], OutputXMR(agent.internal["XMR.3"]).graph(agent)["FETCH.1"]["THEME"].singleton())

        #######

        # 2a) Visual input "Jake leaves"
        agent._input(self.observations()["Jake leaves"], type=XMR.Type.VISUAL.name)

        # 2b) TEST: Jake is no longer in the environment
        with self.assertRaises(Exception):
            agent.env().location("ENV.HUMAN.1")

        # 2c) IIDEA loop
        mock = self.iidea_loop(agent)

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
        agent._input(self.observations()["screwdriver moved to workspace"], type=XMR.Type.VISUAL.name)

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

        # 3g) TEST: An instance of BUILD-A-CHAIR is in progress, with the first second waiting on the physical effector
        self.assertGoalExists(agent, isa="EXE.BUILD-A-CHAIR", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[1].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["FETCH-OBJECT-CAPABILITY"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.internal["XMR.6"], Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["BRACKET.1"], OutputXMR(agent.internal["XMR.6"]).graph(agent)["FETCH.1"]["THEME"].singleton())

        #######

        # 4a) Visual input "Jake returns"
        agent._input(self.observations()["jake enters"], type=XMR.Type.VISUAL.name)

        # 4b) TEST: Jake is in the environment
        self.assertEqual(agent.ontology["LOCATION"], agent.env().location("ENV.HUMAN.1"))

        # 4c) IIDEA loop
        self.iidea_loop(agent)

        # 4d) TEST: An instance of ACKNOWLEDGE-VISUAL-INPUT with the correct VMR was triggered, and executed
        #     TEST: An instance of GREET-AGENT with the correct VMR was created
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#3"])
        self.assertGoalExists(agent, isa="EXE.GREET-AGENT", status=Goal.Status.PENDING, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#3"])

        # 4e) IIDEA loop
        self.iidea_loop(agent)

        # 4f) An instance of GREET-AGENT is in progress, with the first step waiting on the verbal effector
        self.assertGoalExists(agent, isa="EXE.GREET-AGENT", status=Goal.Status.ACTIVE, query=lambda goal: goal.plans()[0].steps()[0].status() == Step.Status.PENDING)
        self.assertFalse(Effector(agent.internal["VERBAL-EFFECTOR.1"]).is_free())
        self.assertEqual(agent.exe["SPEAK-CAPABILITY"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_capability())
        self.assertEqual(agent.internal["XMR.8"], Effector(agent.internal["VERBAL-EFFECTOR.1"]).on_output())
        self.assertEqual(agent.environment["HUMAN.1"], OutputXMR(agent.internal["XMR.8"]).graph(agent)["GREET.1"]["THEME"].singleton())

        fail()

        # 5a) Callback input capability SPEAK("Hi Jake.") is complete
        agent.callback("SELF.CALLBACK.3")

        # 5b) IIDEA loop
        self.iidea_loop(agent)

        # 5c) TEST: ACKNOWLEDGE-HUMAN is "satisfied"
        self.assertTrue(Goal(agent.internal["ACKNOWLEDGE-HUMAN.1"]).is_satisfied())

        # 5d) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 6a) Input from "Jake", "What are you doing?"
        agent._input(self.analyses()[1], source="LT.HUMAN.1")

        # 6b) IIDEA loop
        self.iidea_loop(agent)

        # 6c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-INPUT", status=Goal.Status.PENDING, query=lambda goal: XMR(goal.resolve("$tmr")).graph(agent) == agent["TMR#2"])

        # 6d) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 6e) IIDEA loop
        self.iidea_loop(agent)

        # 6f) TEST: An instance of DECIDE-ON-LANGUAGE-INPUT with the correct TMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.DECIDE-ON-LANGUAGE-INPUT", status=Goal.Status.PENDING, query=lambda goal: XMR(goal.resolve("$tmr")).graph(agent) == "TMR#2")

        # 6g) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 6h) IIDEA loop
        self.iidea_loop(agent)

        # 6i) TEST: An instance of RESPOND-TO-QUERY with the correct TMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.RESPOND-TO-QUERY", status=Goal.Status.PENDING, query=lambda goal: XMR(goal.resolve("$tmr")).graph(agent) == "TMR#2")

        # 6j) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 6k) IIDEA loop
        mock = self.iidea_loop(agent, mock=SpeakCapabilityMP)

        # 6l) TEST: The only VERBAL-EFFECTOR is reserved to RESPOND-TO-QUERY (using capability SPEAK("I am fetching a foot bracket."))
        self.assertEffectorReserved(agent, "SELF.VERBAL-EFFECTOR.1", "SELF.RESPOND-TO-QUERY.1", "EXE.SPEAK-CAPABILITY")
        mock.assert_called_once_with("I am fetching a foot bracket.")

        # 6m) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 7a) Callback input capability SPEAK("I am fetching a foot bracket.") is complete
        agent.callback("SELF.CALLBACK.4")

        # 7b) IIDEA loop
        self.iidea_loop(agent)

        # 7c) TEST: RESPOND-TO-QUERY is "satisfied"
        self.assertTrue(Goal(agent.internal["RESPOND-TO-QUERY.1"]).is_satisfied())

        # 7d) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 8a) Callback input capability GET(foot_bracket)
        agent.callback("SELF.CALLBACK.2")

        # 8b) IIDEA loop
        self.iidea_loop(agent)

        # 8c) TEST: The PHYSICAL-EFFECTOR is released
        self.assertTrue(Effector(agent.internal["PHYSICAL-EFFECTOR.1"]).is_free())

        # 8d) TEST: PERFORM-COMPLEX-TASK is still "active" (the chair is not yet built)
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

