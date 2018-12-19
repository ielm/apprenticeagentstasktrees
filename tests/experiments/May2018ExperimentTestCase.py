from backend.agent import Agent
from backend.models.graph import Network
from backend.models.ontology import Ontology
from backend.utils.FRUtils import format_pretty_htn

from pkgutil import get_data

import json, os, unittest


class ExperimentTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.ontology = self.n.register(Ontology.init_default())

    def test_input(self):
        demo = json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json").decode('ascii'))

        input = [
            demo[0],  # We will build a chair.

            demo[1],  # I need a screwdriver to assemble a chair.
            demo[2],  # Get a screwdriver.

            demo[3],  # First, we will build a front leg of the chair.
            demo[4],  # Get a foot bracket.
            demo[5],  # Get a front bracket.
            demo[6],  # Get a dowel.
            demo[7],  # Hold the dowel.
            demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],  # Release the dowel.
            demo[10],  # We have assembled a front leg.
            # demo[11],  # We finished assembling the chair.
        ]

        agent = Agent(ontology=self.ontology)
        agent.logger().enable()

        print("")
        print("============================================")
        print("")
        for i in input:
            agent.input(i)
            print("")
            #print(agent.wo_memory)
            print("HTN (simplified):")
            print(format_pretty_htn(agent.wo_memory, agent.wo_memory["WM.BUILD.1"], indent=1))
            print("")
            print("============================================")
            print("")

        print(agent.wo_memory)

        expected = get_data("tests.resources", "AgentTestCase_TestInputExpectedOutput.txt").decode('ascii')
        self.assertEqual(expected, format_pretty_htn(agent.wo_memory, agent.wo_memory["WM.BUILD.1"], indent=1))

    def test_ltm(self):
        demo = json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json").decode('ascii'))

        agent = Agent(ontology=self.ontology)
        agent.logger().disable()

        input = [
            demo[0],  # We will build a chair.

            demo[1],  # I need a screwdriver to assemble a chair.
            demo[2],  # Get a screwdriver.

            demo[3],  # First, we will build a front leg of the chair.
            demo[4],  # Get a foot bracket.
            demo[5],  # Get a front bracket.
            demo[6],  # Get a dowel.
            demo[7],  # Hold the dowel.
            demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],  # Release the dowel.
            demo[10],  # We have assembled a front leg.
            demo[11],  # We finished assembling the chair.
        ]

        for i in input:
            agent.input(i)

        print("Long Term Memory BUILD-LT1")
        print(format_pretty_htn(agent.lt_memory, agent.lt_memory["BUILD.1"], indent=1))
        print("========")

        input = [
            demo[0],  # We will build a chair.

            demo[1],  # I need a screwdriver to assemble a chair.
            demo[2],  # Get a screwdriver.

            demo[3],  # First, we will build a front leg of the chair.
            demo[6],  # Get a dowel.
            demo[4],  # Get a foot bracket.
            demo[5],  # Get a front bracket.
            demo[7],  # Hold the dowel.
            demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],  # Release the dowel.
            demo[10],  # We have assembled a front leg.
            demo[11],  # We finished assembling the chair.
        ]

        for i in input:
            agent.input(i)

        print("Long Term Memory BUILD-LT3")
        print(format_pretty_htn(agent.lt_memory, agent.lt_memory["BUILD.3"], indent=1))

        print("")
        print("Action Queue")
        print(agent.action_queue)

        from backend.contexts.ACTContext import ACTContext
        agent.context = ACTContext(agent)

        print("")
        agent.logger().enable()
        agent.input(demo[0])

        print("")
        print("Action Queue")
        print(agent.action_queue)

        self.assertEqual(agent.action_queue, ["ROBOT.GET(ONT.SCREWDRIVER)"])