from models.tmr import TMR
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class TaskModelTestCase(ApprenticeAgentsTestCase):

    def test_is_utterance(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        self.assertTrue(TMR(demo[0]).is_utterance())
        self.assertTrue(TMR(demo[1]).is_utterance())
        self.assertTrue(TMR(demo[3]).is_utterance())
        self.assertTrue(TMR(demo[8]).is_utterance())
        self.assertTrue(TMR(demo[10]).is_utterance())
        self.assertTrue(TMR(demo[11]).is_utterance())
        self.assertTrue(TMR(demo[16]).is_utterance())
        self.assertTrue(TMR(demo[18]).is_utterance())

        self.assertFalse(TMR(demo[2]).is_utterance())
        self.assertFalse(TMR(demo[4]).is_utterance())
        self.assertFalse(TMR(demo[5]).is_utterance())
        self.assertFalse(TMR(demo[6]).is_utterance())
        self.assertFalse(TMR(demo[7]).is_utterance())
        self.assertFalse(TMR(demo[9]).is_utterance())
        self.assertFalse(TMR(demo[12]).is_utterance())
        self.assertFalse(TMR(demo[13]).is_utterance())
        self.assertFalse(TMR(demo[14]).is_utterance())
        self.assertFalse(TMR(demo[15]).is_utterance())
        self.assertFalse(TMR(demo[17]).is_utterance())

    def test_find_themes(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        self.assertEqual(TMR(demo[0]).find_themes(), ["CHAIR"])
        self.assertEqual(TMR(demo[2]).find_themes(), ["TAKE", "SCREWDRIVER"])

    def test_is_postfix(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        self.assertFalse(TMR(demo[0]).is_postfix())
        self.assertFalse(TMR(demo[1]).is_postfix())
        self.assertFalse(TMR(demo[3]).is_postfix())
        self.assertFalse(TMR(demo[8]).is_postfix())
        self.assertTrue(TMR(demo[10]).is_postfix())
        self.assertFalse(TMR(demo[11]).is_postfix())