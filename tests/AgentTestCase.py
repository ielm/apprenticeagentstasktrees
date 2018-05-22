from backend.agent import Agent
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
        ]

        agent = Agent()

        for i in input:
            agent.input(i)

        print(agent.st_memory)