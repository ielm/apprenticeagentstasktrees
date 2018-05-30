from backend.agent import Agent
from backend.utils.FRUtils import format_pretty_htn
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase

import os


class AgentTestCase(ApprenticeAgentsTestCase):

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

        agent = Agent()
        agent.logger().enable()

        print("")
        print("============================================")
        print("")
        for i in input:
            agent.input(i)
            print("")
            #print(agent.wo_memory)
            print("HTN (simplified):")
            print(format_pretty_htn(agent.wo_memory, agent.wo_memory["BUILD-WM1"], indent=1))
            print("")
            print("============================================")
            print("")

        print(agent.wo_memory)

    def test_ltm(self):
        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses.json"
        demo = self.resource(file)

        agent = Agent()
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
        print(format_pretty_htn(agent.lt_memory, agent.lt_memory["BUILD-LT1"], indent=1))
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
        print(format_pretty_htn(agent.lt_memory, agent.lt_memory["BUILD-LT3"], indent=1))