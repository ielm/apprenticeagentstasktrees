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
            # demo[38],   # Finished.
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
            # demo[53],   # Finished.
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
        print(model)
        # print("")
        # print(tm.active_node)

        # self.fail("NYI")