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
            self.resource('resources/actions/get-screwdriver.json'),
            demo[3],
            self.resource('resources/actions/get-bracket-foot.json'),
            self.resource('resources/actions/get-bracket-front.json'),
            self.resource('resources/actions/get-dowel.json'),
            self.resource('resources/actions/hold-dowel.json'),
            demo[8],
            self.resource('resources/actions/release-dowel.json'),
            demo[10],
        ]

        model = TaskModel().learn(Instructions(input))
        print(model)

        self.fail("NYI")