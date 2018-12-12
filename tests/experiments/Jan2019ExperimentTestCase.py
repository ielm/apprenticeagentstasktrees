from backend.agent import Agent
from backend.models.agenda import Goal
from backend.models.bootstrap import Bootstrap
from backend.models.effectors import Capability, Effector
from backend.models.graph import Frame, Identifier
from backend.models.mps import AgentMethod
from backend.models.ontology import Ontology
from backend.models.xmr import XMR

from pkgutil import get_data
from typing import Callable, Type, Union
from unittest.mock import patch

import json
import unittest

from backend.resources.AgentMP import GetPhysicalObjectCapabilityMP, SpeakCapabilityMP


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
        Bootstrap.bootstrap_resource(agent, "backend.resources", "chair.knowledge")

        # Pb) There is an instance of "Jake", who is known, present, and taught the robot the chair instructions
        Bootstrap.bootstrap_resource(agent, "backend.resources.experiments", "Jan2019.1-1.knowledge")

        #######

        # 1a) Input from "Jake", "Let's build a chair."
        agent._input(self.analyses()[0], source="LT.HUMAN.1")

        # 1b) IIDEA loop
        self.iidea_loop(agent)

        # 1c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-INPUT", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$xmr")["REFERS-TO-GRAPH"].singleton() == "TMR#1")

        # 1d) IIDEA loop
        self.iidea_loop(agent)

        # 1e) TEST: An instance of DECIDE-ON-LANGUAGE-INPUT with the correct TMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.DECIDE-ON-LANGUAGE-INPUT", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$tmr")["REFERS-TO-GRAPH"].singleton() == "TMR#1")

        # 1f) IIDEA loop
        self.iidea_loop(agent)

        # 1g) TEST: An instance of PERFORM-COMPLEX-TASK with the LTM instructions root is on the agenda
        self.assertGoalExists(agent, isa="EXE.PERFORM-COMPLEX-TASK", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$task")._identifier == "LT.BUILD.1")

# ====================================================================================== #

        # 2a) Visual input "Jake leaves"
        agent._input(self.observations()["Jake leaves"], type=XMR.Type.VISUAL.name)

        # 2b) IIDEA loop
        mock = self.iidea_loop(agent, mock=GetPhysicalObjectCapabilityMP)

        # 2c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-INPUT", status=Goal.Status.PENDING, query=lambda goal: XMR(goal.resolve("$xmr")).graph(agent) == agent["VMR#1"])

        # 2d) TEST: The only PHYSICAL-EFFECTOR is reserved to PERFORM-COMPLEX-TASK (using capability GET(screwdriver))
        self.assertEffectorReserved(agent, "SELF.PHYSICAL-EFFECTOR.1", "SELF.GOAL.2", "EXE.GET-CAPABILITY")
        mock.assert_called_once_with(agent.lookup("ENV.SCREWDRIVER.1"))

        # 2e) IIDEA loop
        self.iidea_loop(agent)

        # 2f) TEST: An instance of REACT-TO-VISUAL-INPUT with the correct VMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.REACT-TO-VISUAL-INPUT", status=Goal.Status.PENDING, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#1"])

        # 2g) TEST: The PHYSICAL-EFFECTOR is still reserved; PERFORM-COMPLEX-TASK is still "active"
        self.assertEffectorReserved(agent, "SELF.PHYSICAL-EFFECTOR.1", "SELF.GOAL.2", "EXE.GET-CAPABILITY")

        # 2h) IIDEA loop
        self.iidea_loop(agent)

        # 2i) TEST: REACT-TO-VISUAL-INPUT is satisfied (only 2 goals: FSTD and PERFORM-COMPLEX-TASK)
        self.assertGoalExists(agent, isa="EXE.REACT-TO-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#1"])

        # 2j) TEST: The environment no longer registers "Jake" as being present
        # Might need to be frame rather than name
        self.assertNotIn("ENV.HUMAN.1", agent.env().current())

        # 2k) TEST: The PHYSICAL-EFFECTOR is still reserved; PERFORM-COMPLEX-TASK is still "active"
        self.assertEffectorReserved(agent, "SELF.PHYSICAL-EFFECTOR.1", "SELF.GOAL.2", "EXE.GET-CAPABILITY")

        # 3a) Callback input capability GET(screwdriver) is complete
        agent.callback("SELF.CALLBACK.1")

        # 3b) Visual input "the screwdriver has been moved"
        agent._input(self.observations()["Screwdriver moves close"], type=XMR.Type.VISUAL.name)

        # 3c) TEST: The screwdriver is "close" to the agent
        # TODO - Change test to reflect location changes
        self.assertEqual(agent.env().graph['ENV.EPOCH.1']["LOCATION"][0].resolve()["RANGE"].singleton(), agent.env().location("ENV.SCREWDRIVER.1"))

        # 3d) IIDEA loop
        mock = self.iidea_loop(agent, mock=GetPhysicalObjectCapabilityMP)

        # 3e) TEST: An instance of ACKNOWLEDGE-INPUT with the correct VMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-INPUT", status=Goal.Status.PENDING, query=lambda goal: XMR(goal.resolve("$xmr")).graph(agent) == agent["VMR#2"])

        # 3f) TEST: The only PHYSICAL-EFFECTOR is reserved to PERFORM-COMPLEX-TASK (using capability GET(foot_bracket))
        # TODO - call GetPhysicalObjectCapabilityMP with ENV.BRACKET.1
        self.assertEffectorReserved(agent, "SELF.PHYSICAL-EFFECTOR.1", "SELF.GOAL.2",  "EXE.GET-CAPABILITY")
        mock.assert_called_once_with("ENV.BRACKET.1")

        # 3g) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["SELF.GOAL.2"]).is_active())

        # 3h) IIDEA loop
        self.iidea_loop(agent)
        mock.assert_called_once_with(agent.lookup("ENV.SCREWDRIVER.1"))

        # 3i) TEST: An instance of REACT-TO-VISUAL-INPUT with the correct VMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.REACT-TO-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#2"])

        # 3j) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 3k) IIDEA loop
        self.iidea_loop(agent)

        # 3l) TEST: All instances of REACT-TO-VISUAL-INPUT are satisfied
        self.assertEqual(0, len(list(filter(lambda g: not g.is_satisfied(), map(lambda g: Goal(g), agent.internal.search(Frame.q(agent).isa("EXE.REACT-TO-VISUAL-INPUT")))))))

        # 3j) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 4a) Visual input "Jake returns"
        agent._input(self.observations()["jake enters"], type=XMR.Type.VISUAL.name)

        # 4b) IIDEA loop
        self.iidea_loop(agent)

        # 4c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-INPUT", status=Goal.Status.PENDING, query=lambda goal: XMR(goal.resolve("$tmr")).graph(agent) == agent["VMR#3"])

        # 4d) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 4e) IIDEA loop
        self.iidea_loop(agent)

        # 4f) TEST: An instance of REACT-TO-VISUAL-INPUT with the correct VMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.REACT-TO-VISUAL-INPUT", status=Goal.Status.SATISFIED, query=lambda goal: XMR(goal.resolve("$vmr")).graph(agent) == agent["VMR#3"])

        # 4g) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 4h) IIDEA loop
        self.iidea_loop(agent)

        # 4i) TEST: An instance of ACKNOWLEDGE-HUMAN with the correct @human instance is on the agenda
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-HUMAN", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$human")._identifier == "ENV.HUMAN.1")

        # 4j) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

        # 4k) IIDEA loop
        mock = self.iidea_loop(agent, mock=SpeakCapabilityMP)

        # 4l) TEST: The only VERBAL-EFFECTOR is reserved to ACKNOWLEDGE-HUMAN (using capability SPEAK("Hi Jake."))
        self.assertEffectorReserved(agent, "SELF.VERBAL-EFFECTOR.1", "SELF.ACKNOWLEDGE-HUMAN.1", "EXE.SPEAK-CAPABILITY")
        mock.assert_called_once_with("Hi Jake.")

        # 4m) TEST: ACKNOWLEDGE-HUMAN is "active"
        self.assertTrue(Goal(agent.internal["ACKNOWLEDGE-HUMAN.1"]).is_active())

        # 4n) TEST: PERFORM-COMPLEX-TASK is still "active"
        self.assertTrue(Goal(agent.internal["PERFORM-COMPLEX-TASK.1"]).is_active())

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

