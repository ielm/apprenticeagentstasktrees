from backend.agent import Agent
from backend.models.graph import Network
from backend.models.ontology import Ontology
from backend.utils.FRUtils import format_pretty_htn

import json, os, unittest


class AnotherLegTestCase(unittest.TestCase):
    """
    Test demo input sequence for all another leg.
    """

    def setUp(self):
        self.n = Network()
        self.ontology = self.n.register(Ontology.init_default())

    def resource(self, fp):
        r = None
        with open(fp) as f:
            r = json.load(f)
        return r

    def test_input(self):
        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses_ext.json"
        # file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses_I-ASSEMBLED.json"
        # file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses_WE-BUILT.json"
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
            demo[11],  # Now, we will build another front leg.
            demo[12],  # Get another foot bracket.
            demo[13],  # Get another front bracket.
            demo[14],  # Get another dowel.
            demo[15],  # Hold the dowel.
            demo[16],  # I am putting another set of brackets of the dowel.
            demo[17],  # Release the dowel.
            demo[18]  # I have assembled another front chair leg
            # demo[19], # Now, we will build the back leg on the right side.
            # demo[20], # Get another foot bracket.
            # demo[21], # Get the back bracket on the right side.
            # demo[22], # Get another dowel.
            # demo[23], # Hold the dowel.
            # demo[24], # I am putting the third set of brackets on a dowel.
            # demo[25], # Release the dowel.
            # demo[26]  # I have assembled the back leg on the right side of the chair.
            # # demo[27]  # We finished assembling the chair.
        ]

        # print(demo[11]["sentence"])

        agent = Agent(ontology=self.ontology)
        agent.logger().enable()

        # agent.logger().disable()

        print("\n========================================\n")
        for i in input:
            agent.input(i)
            print("\n\n")
            print("HTN (simplified):")
            print(format_pretty_htn(agent.wo_memory, agent.wo_memory["WM.BUILD.1"], indent=1))
            print("")
            print("============================================")
            print("")
        print(agent.wo_memory)
        print("=" * 80)

    # def test_ltm(self):
    #     file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses_ext.json"
    #     demo = self.resource(file)

    #     agent = Agent(ontology=self.ontology)
    #     # agent.logger().disable()
    #     agent.logger().enable()

    #     input = [
    #         demo[0],  # We will build a chair.

    #         demo[1],  # I need a screwdriver to assemble a chair.
    #         demo[2],  # Get a screwdriver.

    #         demo[3],  # First, we will build a front leg of the chair.
    #         demo[4],  # Get a foot bracket.
    #         demo[5],  # Get a front bracket.
    #         demo[6],  # Get a dowel.
    #         demo[7],  # Hold the dowel.
    #         demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
    #         demo[9],  # Release the dowel.
    #         demo[10], # We have assembled a front leg.
    #         demo[11], # Now, another front leg.
    #         demo[12], # Get another foot bracket.
    #         demo[13], # Get another front bracket.
    #         demo[14], # Get another dowel.
    #         demo[15], # Hold the dowel.
    #         demo[16], # I am putting another set of brackets of the dowel.
    #         demo[17], # Release the dowel.
    #         demo[18], # I have assembled another front chair leg
    #         demo[19]
    #     ]
    #     for i in input:
    #         agent.input(i)
    #         print("\n\n")

    #     print("\nLong Term Memory BUILD-LT1\n")
    #     print(format_pretty_htn(agent.lt_memory, agent.lt_memory["BUILD.1"], indent=1))
    #     print("========")

    # print("")
    # print("Action Queue")
    # print(agent.action_queue)

    # from backend.contexts.ACTContext import ACTContext
    # agent.context = ACTContext(agent)

    # print("")
    # agent.logger().enable()

    # agent.input(demo[0])
    # print("")
    # print("Action Queue")
    # print(agent.action_queue)

    # print("Action Queue")
    # for i in input:
    #     agent.input(i)
    #     print(agent.action_queue)
