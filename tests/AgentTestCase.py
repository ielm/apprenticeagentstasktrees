from backend.agent import Agent
from backend.models.graph import Network
from backend.models.ontology import Ontology
from backend.utils.FRUtils import format_pretty_htn

import json
import os
import unittest


class AgentTestCase(unittest.TestCase): # TODO: Clean up AATestCase and move back to that

    def setUp(self):
        self.n = Network()
        self.ontology = self.n.register(Ontology.init_default())

    def resource(self, fp):
        r = None
        with open(fp) as f:
            r = json.load(f)
        return r

    def test_input(self):
        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses.json"
        demo = self.resource(file)

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

        agent = Agent(self.n, ontology=self.ontology)
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

        with open(os.path.abspath(__package__) + "/resources/AgentTestCase_TestInputExpectedOutput.txt", 'r') as expected:
            expected = expected.read()
            self.assertEqual(expected, format_pretty_htn(agent.wo_memory, agent.wo_memory["WM.BUILD.1"], indent=1))

    def test_ltm(self):
        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses.json"
        demo = self.resource(file)

        agent = Agent(self.n, ontology=self.ontology)
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