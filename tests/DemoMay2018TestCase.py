import json
from taskmodel import TaskModel
from instructions import Instructions
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class DemoMay2018TestCase(ApprenticeAgentsTestCase):

    def test_demo(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        input = [
            demo[0],    # We will build a chair.
            demo[1],    # I need a screwdriver to assemble the chair.
            demo[2],    # Get a screwdriver.
            demo[3],    # First, we will build a front leg of the chair.
            demo[4],    # Get a foot bracket.
            demo[5],    # Get a front bracket.
            demo[6],    # Get a dowel.
            demo[7],    # Hold the dowel.
            demo[8],    # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],    # Release the dowel.
            demo[10],   # We have assembled a front leg.
            demo[11],   # Now, another front leg.
            demo[12],   # Get another foot bracket.
            demo[13],   # Get another front bracket.
            demo[14],   # Get another dowel.
            demo[15],   # Hold the dowel.
            demo[16],   # I am putting another set of brackets on the dowel.
            demo[17],   # Release the dowel.
            demo[18],   # I have assembled another front chair leg.
        ]

        model = TaskModel().learn(Instructions(input))
        print(model)

        # self.fail("NYI")