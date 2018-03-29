import json
from taskmodel import TaskModel
from instructions import Instructions
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class TaskModelTestCase(ApprenticeAgentsTestCase):

    def test_demo(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        input = [
            demo[0],
            demo[1],
            demo[2],
            demo[3],
            demo[4],
            demo[5],
            demo[6],
            demo[7],
            demo[8],
            demo[9],
            demo[10],
        ]

        model = TaskModel().learn(Instructions(input))
        print(model)

        self.fail("NYI")