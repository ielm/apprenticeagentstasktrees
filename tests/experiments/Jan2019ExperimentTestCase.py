from backend.agent import Agent
from backend.models.agenda import Goal
from backend.models.bootstrap import Bootstrap
from backend.models.ontology import Ontology

from pkgutil import get_data
from typing import Callable

import json
import unittest


class Jan2019Experiment(unittest.TestCase):

    def analyses(self):
        return json.loads(get_data("tests.resources", "DemoJan2019_Analyses.json").decode('ascii'))

    def iidea_loop(self, agent: Agent):
        if agent.IDEA._stage == Agent.IDEA.D:
            agent.iidea()
        while agent.IDEA._stage != Agent.IDEA.D:
            agent.iidea()

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

    def test_1_1(self):

        agent = Agent(ontology=Ontology.init_default())

        #######

        # Pa) Load LTM with the chair building instructions
        Bootstrap.bootstrap_resource(agent, "backend.resources", "chair.knowledge")

        # Pb) There is an instance of "Jake", who is known, present, and taught the robot the chair instructions
        Bootstrap.bootstrap_resource(agent, "backend.resources.experiments", "Jan2019.1-1.knowledge")

        #######

        # 1a) Input from "Jake", "Let's build a chair."
        agent._input(self.analyses()[0])

        # 1b) IIDEA loop
        self.iidea_loop(agent)

        # 1c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.ACKNOWLEDGE-INPUT", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$tmr")["REFERS-TO-GRAPH"].singleton() == "TMR#1")

        # 1d) IIDEA loop
        self.iidea_loop(agent)

        # 1e) TEST: An instance of DECIDE-ON-LANGUAGE-INPUT with the correct TMR is on the agenda
        self.assertGoalExists(agent, isa="EXE.DECIDE-ON-LANGUAGE-INPUT", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$tmr")["REFERS-TO-GRAPH"].singleton() == "TMR#1")

        # 1f) IIDEA loop
        self.iidea_loop(agent)

        # 1g) TEST: An instance of PERFORM-COMPLEX-TASK with the LTM instructions root is on the agenda
        self.assertGoalExists(agent, isa="EXE.PERFORM-COMPLEX-TASK", status=Goal.Status.PENDING, query=lambda goal: goal.resolve("$task").singleton() == "LT.BUILD.1")

        # 2a) Visual input "Jake leaves"
        # 2b) IIDEA loop
        # 2c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        # 2d) TEST: The only PHYSICAL-EFFECTOR is reserved to PERFORM-COMPLEX-TASK (using capability GET(screwdriver))
        # 2e) IIDEA loop
        # 2f) TEST: An instance of REACT-TO-VISUAL-INPUT with the correct VMR is on the agenda
        # 2g) TEST: The PHYSICAL-EFFECTOR is still reserved; PERFORM-COMPLEX-TASK is still "active"
        # 2h) IIDEA loop
        # 2i) TEST: REACT-TO-VISUAL-INPUT is satisfied (only 2 goals: FSTD and PERFORM-COMPLEX-TASK)
        # 2j) TEST: The PHYSICAL-EFFECTOR is still reserved; PERFORM-COMPLEX-TASK is still "active"

        # 3a) Callback input capability GET(screwdriver) is complete
        # 3b) MOCK: The status of the screwdriver must be changed in WM (to reflect what would happen in a real environment)
        #           Should we have an ENV graph?  Probably.
        # 3c) IIDEA loop
        # 3d) TEST: The only PHYSICAL-EFFECTOR is reserved to PERFORM-COMPLEX-TASK (using capability GET(foot_bracket))
        # 3e) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 4a) Visual input "Jake returns"
        # 4b) IIDEA loop
        # 4c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        # 4d) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 4e) IIDEA loop
        # 4f) TEST: An instance of REACT-TO-VISUAL-INPUT with the correct VMR is on the agenda
        # 4g) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 4h) IIDEA loop
        # 4i) TEST: An instance of ACKNOWLEDGE-HUMAN with the correct @human instance is on the agenda
        # 4j) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 4k) IIDEA loop
        # 4l) TEST: The only VERBAL-EFFECTOR is reserved to ACKNOWLEDGE-HUMAN (using capability SPEAK("Hi Jake."))
        # 4m) TEST: ACKNOWLEDGE-HUMAN is "active"
        # 4n) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 5a) Callback input capability SPEAK("Hi Jake.") is complete
        # 5b) IIDEA loop
        # 5c) TEST: ACKNOWLEDGE-HUMAN is "satisfied"
        # 5d) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 6a) Input from "Jake", "What are you doing?"
        # 6b) IIDEA loop
        # 6c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        # 6d) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 6e) IIDEA loop
        # 6f) TEST: An instance of DECIDE-ON-LANGUAGE-INPUT with the correct TMR is on the agenda
        # 6g) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 6h) IIDEA loop
        # 6i) TEST: An instance of RESPOND-TO-QUERY with the LTM instructions root is on the agenda
        # 6j) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 6k) IIDEA loop
        # 6l) TEST: The only VERBAL-EFFECTOR is reserved to RESPOND-TO-QUERY (using capability SPEAK("I am fetching a foot bracket."))
        # 6m) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 7a) Callback input capability SPEAK("I am fetching a front bracket.") is complete
        # 7b) IIDEA loop
        # 7c) TEST: RESPOND-TO-QUERY is "satisfied"
        # 7d) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 8a) Callback input capability GET(foot_bracket)
        # 8b) IIDEA loop
        # 8c) TEST: The PHYSICAL-EFFECTOR is released
        # 8d) TEST: PERFORM-COMPLEX-TASK is still "active" (the chair is not yet built)

        self.fail()

