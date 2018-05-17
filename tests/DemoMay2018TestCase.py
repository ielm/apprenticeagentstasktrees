import os
import unittest

from backend.taskmodel import TaskModel
from models.instructions import Instructions
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class DemoMay2018TestCase(ApprenticeAgentsTestCase):

    @unittest.skip("This requires both the ontosem and corenlp service to be running, otherwise it will fail.")
    def test_rearranged(self):
        from backend.config import networking
        networking["ontosem-port"] = "5001"

        input = [
            ["u", "We will build a chair."],
                ["u", "I need a screwdriver to assemble a chair."],
                    ["a", "get-screwdriver"],
                ["u", "Now we will assemble the seat."],
                    ["u", "First, we will build the front leg of the chair."],
                        ["a", "get-bracket-foot"],
                        ["a", "get-bracket-front"],
                        ["a", "get-dowel"],
                        ["a", "hold-dowel"],
                        ["u", "I am using the screwdriver to affix the brackets on the dowel with screws."],
                        ["a", "release-dowel"],
                    ["u", "We have assembled a front leg."],
                    ["u", "Now, another front leg."],
                        ["a", "get-bracket-foot"],
                        ["a", "get-bracket-front"],
                        ["a", "get-dowel"],
                        ["a", "hold-dowel"],
                        ["u", "I am putting another set of brackets on the dowel."],
                        ["a", "release-dowel"],
                    ["u", "I have assembled another front chair leg."],
                    ["u", "Now, the back leg on the right side."],
                        ["a", "get-bracket-foot"],
                        ["a", "get-bracket-back-right"],
                        ["a", "get-dowel"],
                        ["a", "hold-dowel"],
                        ["u", "I am putting the third set of brackets on a dowel."],
                        ["a", "release-dowel"],
                    ["u", "I have assembled the back leg on the right side of the chair."],
                        ["a", "get-bracket-foot"],
                        ["a", "get-bracket-back-left"],
                        ["a", "get-dowel"],
                        ["a", "hold-dowel"],
                        ["u", "I am putting the fourth set of brackets on a dowel."],
                        ["a", "release-dowel"],
                    ["u", "I have assembled the back leg on the left side of the chair"],
                    ["u", "Now we affix the legs to the seat."],
                        ["a", "get-seat"],
                        ["a", "hold-seat"],
                        ["u", "I am affixing the four legs to the seat."],
                    ["u", "Finished."],
                ["u", "We have assembled the seat."],
                ["u", "Now we will assemble the back."],
                    ["u", "First, we assemble the top of the back."],
                        ["a", "get-top-bracket"],
                        ["a", "get-top-bracket"],
                        ["a", "get-top-dowel"],
                        ["a", "hold-top-dowel"],
                        ["u", "I am affixing the top brackets on the top dowel."],
                        ["a", "release-top-dowel"],
                    ["u", "We have assembled the top of the back."],
                    ["u", "Now, we affix the verticals."],
                        ["u", "We will affix a vertical piece."],
                            ["a", "get-dowel"],
                            ["a", "hold-dowel"],
                            ["u", "I am inserting this dowel into the back bracket on the right side to make one vertical piece."],
                        ["u", "I have made one vertical piece."],
                        ["u", "We will affix another vertical piece."],
                            ["a", "get-dowel"],
                            ["a", "hold-dowel"],
                            ["u", "I am inserting the dowel into the back bracket on the left side to make another vertical piece."],
                        ["u", "I have made another vertical piece."],
                        ["u", "Now we must affix the back to the vertical pieces."],
                            ["a", "get-back"],
                            ["a", "hold-back"],
                            ["u", "I am affixing the back to the vertical pieces."],
                        ["u", "We have affixed the back."],
                    ["u", "Done with the verticals."],
                    ["u", "Now, we affix the top brackets to the back of the chair."],
                        ["a", "hold-back"],
                        ["u", "I am affixing the top brackets to the back of the chair."],
                        ["u", "Release the back."],
                        ["u", "Finished."],
                    ["u", "We have affixed the top brackets to the back of the chair."],
                ["u", "We have assembled the back of the chair."],
            ["u", "We finished assembling the chair."]
        ]

        from backend.utils.YaleUtils import input_to_tmrs

        tm = TaskModel()
        model = tm.learn(Instructions(input_to_tmrs(input)))

        # print(model)

        from backend.models.tmr import TMR
        tmr = TMR(input_to_tmrs([["u", "We will build the back first."]])[0])
        model = tm.query(tmr)

        # print(model)

        with open("resources/DemoMay2018_RearrangedOutput.txt", "r") as file:
            expected = file.read()
            self.assertEqual(str(model), expected)

    def test_demo(self):
        file = os.path.abspath(__package__) + "/resources/DemoMay2018_TMRs.json"
        demo = self.resource(file)

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

            demo[19],   # Now, the back leg on the right side.
            demo[20],   # Get another foot bracket.
            demo[21],   # Get the back bracket on the right side.
            demo[22],   # Get another dowel.
            demo[23],   # Hold the dowel.
            demo[24],   # I am putting the third set of brackets on a dowel.
            demo[25],   # Release the dowel.
            demo[26],   # I have assembled the back leg on the right side of the chair.

            demo[27],   # Get the foot bracket.
            demo[28],   # Get the back bracket on the left side.
            demo[29],   # Get another dowel.
            demo[30],   # Hold the dowel.
            demo[31],   # I am putting the fourth set of brackets on a dowel.
            demo[32],   # Release the dowel.
            demo[33],   # I have assembled the back leg on the left side of the chair.

            demo[34],   # Now we will assemble the seat.
            demo[35],   # Get the seat.
            demo[36],   # Hold the seat.
            demo[37],   # I am affixing the four legs to the seat.
            demo[38],   # Finished.
            demo[39],   # We have assembled the seat.

            demo[40],   # Now we need to assemble the back.

            demo[41],   # First, we assemble the top of the back.
            demo[42],   # Get a top bracket.
            demo[43],   # Get another top bracket.
            demo[44],   # Get the top dowel.
            demo[45],   # Hold the top dowel.
            demo[46],   # I am affixing the top brackets on the top dowel.
            demo[47],   # Release the top dowel.
            demo[48],   # We have assembled the top of the back.

            demo[49],   # Next, we assemble the back of the chair.
            demo[50],   # Get the back.
            demo[51],   # Hold the back.
            demo[52],   # I am affixing the top bracket to the back of the chair.
            demo[53],   # Finished.
            demo[54],   # We have affixed the top bracket to the back of the chair.
            demo[55],   # We have assembled the back of the chair.

            demo[56],   # We have assembled the back.

            demo[57],   # Now, we affix the verticals.
            demo[58],   # Get a dowel.
            demo[59],   # I am inserting this dowel into the back bracket on the right side to make one vertical piece.
            demo[60],   # I have made one vertical piece.
            demo[61],   # And another vertical piece.
            demo[62],   # Get a dowel.
            demo[63],   # I am inserting this dowel into the back bracket on the left side to make another vertical piece.
            demo[64],   # Done with the verticals.

            demo[65],   # Now were must affix the back to the vertical pieces.
            demo[66],   # I am affixing the back to the seat.
            demo[67],   # We are done.

            demo[68],   # We finished assembling the chair.
        ]

        tm = TaskModel()
        model = tm.learn(Instructions(input))

        with open("resources/DemoMay2018_ExpectedOutput.txt", "r") as file:
            expected = file.read()
            self.assertEqual(str(model), expected)

        from backend.models.tmr import TMR
        model = tm.query(TMR(demo[69]))
        print(model)

    def test_multiple_trees(self):
        file = os.path.abspath(__package__) + "/resources/DemoMay2018_TMRs.json"
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
        print(model)

        with open("resources/DemoMay2018_IntegratedLearning_ExpectedOutput.txt", "r") as file:
            expected = file.read()
            self.assertEqual(str(model), expected)

    @unittest.skip("This requires both the ontosem and corenlp service to be running, otherwise it will fail.")
    def test_integration_full_demo(self):

        from backend.treenode import TreeNode
        TreeNode.id = 0

        input = [
            ["u", "We will build a chair."],
            ["u", "I need a screwdriver to assemble a chair."],  # ["u", "I need a screwdriver to assemble the chair."],
            ["a", "get-screwdriver"],
            ["u", "First, we will build the front leg of the chair."],  # ["u", "First, we will need to build the front leg of the chair."],
            ["a", "get-bracket-foot"],
            ["a", "get-bracket-front"],
            ["a", "get-dowel"],
            ["a", "hold-dowel"],
            ["u", "I am using the screwdriver to affix the brackets on the dowel with screws."],
            ["a", "release-dowel"],
            ["u", "We have assembled a front leg."],
            ["u", "Now, another front leg."],
            ["a", "get-bracket-foot"],
            ["a", "get-bracket-front"],
            ["a", "get-dowel"],
            ["a", "hold-dowel"],
            ["u", "I am putting another set of brackets on the dowel."],
            ["a", "release-dowel"],
            ["u", "I have assembled another front chair leg."],
            ["u", "Now, the back leg on the right side."],
            ["a", "get-bracket-foot"],
            ["a", "get-bracket-back-right"],
            ["a", "get-dowel"],
            ["a", "hold-dowel"],
            ["u", "I am putting the third set of brackets on a dowel."],
            ["a", "release-dowel"],
            ["u", "I have assembled the back leg on the right side of the chair."],
            ["a", "get-bracket-foot"],
            ["a", "get-bracket-back-left"],
            ["a", "get-dowel"],
            ["a", "hold-dowel"],
            ["u", "I am putting the fourth set of brackets on a dowel."],
            ["a", "release-dowel"],
            ["u", "I have assembled the back leg on the left side of the chair"],
            ["u", "Now we will assemble the seat."],
            ["a", "get-seat"],
            ["a", "hold-seat"],
            ["u", "I am affixing the four legs to the seat."],
            ["u", "Finished."],  # ["u", "finished"],
            ["u", "We have assembled the seat."],
            ["u", "Now we will assemble the back."],  # ["u", "Now we need to assemble the back."],  # Not included?
            ["u", "First, we assemble the top of the back."],
            ["a", "get-top-bracket"],
            ["a", "get-top-bracket"],
            ["a", "get-top-dowel"],
            ["a", "get-top-dowel"],
            ["a", "hold-top-dowel"],
            ["u", "I am affixing the top brackets on the top dowel."],
            ["a", "release-top-dowel"],
            ["u", "We have assembled the top of the back."],
            ["u", "Next, we assemble the back of the chair."],
            ["a","get-back"],
            ["a", "hold-back"],
            ["u", "I am affixing the top bracket to the back of the chair."],
            ["u", "Finished."],
            ["u", "We have affixed the top bracket to the back of the chair."],
            ["u", "We have assembled the back of the chair."],
            ["u", "We have assembled the back."],
            ["u", "Now, we affix the verticals."],
            ["a", "get-dowel"],
            ["u", "I am inserting this dowel into the back bracket on the right side to make one vertical piece."],
            ["u", "I have made one vertical piece."],
            ["u", "We will affix another vertical piece."],  # ["u", "And another vertical piece."],
            ["a", "get-dowel"],
            ["u", "I am inserting the dowel into the back bracket on the left side to make another vertical piece."],
            ["u", "Done with the verticals."],
            ["u", "Now we must affix the back to the vertical pieces."],  # ["u", "Now were must affix the back to the vertical pieces."],
            ["u", "I am affixing the back to the seat."],
            ["u", "We are done."],
            ["u", "We finished assembling the chair."]
        ]

        from backend.main import app
        app = app.test_client()

        from backend.config import networking
        networking["ontosem-port"] = "5001"

        from backend.treenode import TreeNode
        TreeNode.id = 1

        import json
        rv = app.post("/learn", data=json.dumps(input), content_type='application/json')
        tree = json.loads(rv.data)

        with open("resources/YaleFormatCompleteOutput.json", "r") as file:
            expected = file.read()
            self.assertEqual(tree, json.loads(expected))