from backend.agent import Agent
from backend.models.graph import Network
from backend.models.ontology import Ontology
from backend.utils.FRUtils import format_pretty_htn

import json, os, unittest

class SystemTestCase(unittest.TestCase):

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

        # Input TMRs
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

        # Pretty print the inputs
        # print(json.dumps(demo[0], indent=2))

        # Initialize Agent
        agent = Agent(ontology=self.ontology)

        # Enable Agent Logger
        agent.logger().enable()

        for i in input:
            agent.input(i)
            print("\n")
            print("HTN (Simplified):")
            print(format_pretty_htn(agent.wo_memory, agent.wo_memory["WM.BUILD.1"], indent=1))
            print("===========================================\n")


        print(agent.wo_memory)














