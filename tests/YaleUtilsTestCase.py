import json
import os

from backend.models.instructions import Instructions
from backend.taskmodel import TaskModel
from backend.treenode import TreeNode
from backend.utils.YaleUtils import format_treenode_yale
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class DemoMay2018TestCase(ApprenticeAgentsTestCase):

    def test_simple_format(self):

        TreeNode.id = 0

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

        tm = TaskModel()
        model = tm.learn(Instructions(input))

        output = format_treenode_yale(model)

        with open("resources/YaleFormatSimple.json", "r") as file:
            expected = file.read()
            self.assertEqual(output, json.loads(expected))

    def test_multiple_integrated(self):

        TreeNode.id = 0

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

        tm = TaskModel()
        model = tm.learn(Instructions(input))

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

        model = tm.learn(Instructions(input))

        output = format_treenode_yale(model)

        with open("resources/YaleFormatIntegrated.json", "r") as file:
            expected = file.read()
            self.assertEqual(output, json.loads(expected))
