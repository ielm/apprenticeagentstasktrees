from backend.tmrutils import find_themes
from backend.tmrutils import is_utterance
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class TaskModelTestCase(ApprenticeAgentsTestCase):

    def test_is_utterance(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        self.assertTrue(is_utterance(demo[0]["results"][0]["TMR"]))
        self.assertTrue(is_utterance(demo[1]["results"][0]["TMR"]))
        self.assertTrue(is_utterance(demo[3]["results"][0]["TMR"]))

        self.assertFalse(is_utterance(demo[2]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[4]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[5]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[6]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[7]["results"][0]["TMR"]))

    def test_find_themes(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        self.assertEqual(find_themes(demo[0]["results"][0]["TMR"]), ["CHAIR"])
        self.assertEqual(find_themes(demo[2]["results"][0]["TMR"]), ["TAKE", "SCREWDRIVER"])