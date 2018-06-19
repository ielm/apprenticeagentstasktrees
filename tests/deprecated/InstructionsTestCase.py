# from models.instructions import Instructions
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase

from unittest import skip


@DeprecationWarning
@skip
class InstructionsTestCase(ApprenticeAgentsTestCase):

    def setUp(self):
        demo = self.resource('resources/DemoMay2018_Analyses.json')

        self.tmr1 = demo[0]
        self.tmr2 = demo[1]
        self.tmr3 = demo[3]

        self.action1 = demo[2]
        self.action2 = demo[4]
        self.action3 = demo[5]

    @skip
    def test_tmr_sequence(self):
        ins = Instructions([
            self.tmr1, self.tmr2, self.tmr3
        ])

        results = list(ins)

        self.assertEqual(results, [[self.tmr1], [self.tmr2], [self.tmr3]])

    @skip
    def test_action_sequence(self):
        ins = Instructions([
            self.action1, self.action2, self.action3
        ])

        results = list(ins)

        self.assertEqual(results, [[self.action1, self.action2, self.action3]])

    @skip
    def test_mixed_sequence(self):
        ins = Instructions([
            self.tmr1, self.action1, self.tmr2, self.action2, self.action3, self.tmr3
        ])

        results = list(ins)

        self.assertEqual(results, [[self.tmr1], [self.action1], [self.tmr2], [self.action2, self.action3], [self.tmr3]])