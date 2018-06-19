import json
import os

from backend.agent import Agent
from backend.models.graph import Network
from backend.models.ontology import Ontology
from backend.utils.YaleUtils import format_learned_event_yale
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase

from unittest import skip


class YaleUtilsTestCase(ApprenticeAgentsTestCase):

    def test_simple_format(self):

        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses.json"
        demo = self.resource(file)

        input = [
            demo[0],  # We will build a chair.

            demo[3],  # First, we will build a front leg of the chair.
            demo[4],  # Get a foot bracket.
            demo[5],  # Get a front bracket.
            demo[6],  # Get a dowel.
            demo[7],  # Hold the dowel.
            demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],  # Release the dowel.
            demo[10],  # We have assembled a front leg.

            # demo[68],  # We finished assembling the chair.
        ]

        n = Network()
        ontology = n.register(Ontology.init_default())

        agent = Agent(n, ontology=ontology)
        for i in input:
            agent.input(i)

        output = format_learned_event_yale(agent.wo_memory["WM.BUILD.1"], ontology)

        self.assertEqual(output, self.load_resource("tests.resources", "YaleFormatSimple.json", parse_json=True))

    @skip
    def test_multiple_integrated(self):

        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses.json"
        demo = self.resource(file)

        input = [
            demo[0],  # We will build a chair.

            demo[3],  # First, we will build a front leg of the chair.
            demo[4],  # Get a foot bracket.
            demo[5],  # Get a front bracket.
            demo[6],  # Get a dowel.
            demo[7],  # Hold the dowel.
            demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],  # Release the dowel.
            demo[10],  # We have assembled a front leg.

            demo[68],  # We finished assembling the chair.
        ]

        n = Network()
        ontology = n.register(Ontology.init_default())

        agent = Agent(n, ontology=ontology)
        for i in input:
            agent.input(i)

        input = [
            demo[0],  # We will build a chair.

            demo[3],  # First, we will build a front leg of the chair.
            demo[6],  # Get a dowel.
            demo[5],  # Get a front bracket.
            demo[4],  # Get a foot bracket.
            demo[7],  # Hold the dowel.
            demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],  # Release the dowel.
            demo[10],  # We have assembled a front leg.

            demo[68],  # We finished assembling the chair.
        ]

        for i in input:
            agent.input(i)

        output = format_treenode_yale(model)

        with open("resources/YaleFormatIntegrated.json", "r") as file:
            expected = file.read()
            self.assertEqual(output, json.loads(expected))
