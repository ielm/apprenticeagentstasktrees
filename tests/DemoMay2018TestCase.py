import json
from taskmodel import TaskModel
from instructions import Instructions
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class TaskModelTestCase(ApprenticeAgentsTestCase):

    def test_x(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        input = [
            demo[0],
            demo[1],
            self.resource('resources/actions/get-screwdriver.json'),
            demo[3],
        ]

        model = TaskModel().learn(Instructions(input))
        print(model)

        self.fail("NYI")