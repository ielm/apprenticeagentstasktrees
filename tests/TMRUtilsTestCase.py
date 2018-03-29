from backend.tmrutils import find_themes
from backend.tmrutils import is_postfix
from backend.tmrutils import is_utterance
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class TaskModelTestCase(ApprenticeAgentsTestCase):

    def test_is_utterance(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        self.assertTrue(is_utterance(demo[0]["results"][0]["TMR"]))
        self.assertTrue(is_utterance(demo[1]["results"][0]["TMR"]))
        self.assertTrue(is_utterance(demo[3]["results"][0]["TMR"]))
        self.assertTrue(is_utterance(demo[8]["results"][0]["TMR"]))
        self.assertTrue(is_utterance(demo[10]["results"][0]["TMR"]))
        self.assertTrue(is_utterance(demo[11]["results"][0]["TMR"]))
        self.assertTrue(is_utterance(demo[16]["results"][0]["TMR"]))
        self.assertTrue(is_utterance(demo[18]["results"][0]["TMR"]))

        self.assertFalse(is_utterance(demo[2]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[4]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[5]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[6]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[7]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[9]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[12]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[13]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[14]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[15]["results"][0]["TMR"]))
        self.assertFalse(is_utterance(demo[17]["results"][0]["TMR"]))

    def test_find_themes(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        self.assertEqual(find_themes(demo[0]["results"][0]["TMR"]), ["CHAIR"])
        self.assertEqual(find_themes(demo[2]["results"][0]["TMR"]), ["TAKE", "SCREWDRIVER"])

    def test_is_postfix(self):
        demo = self.resource('resources/DemoMay2018_TMRs.json')

        self.assertFalse(is_postfix(demo[0]["results"][0]["TMR"]))
        self.assertFalse(is_postfix(demo[1]["results"][0]["TMR"]))
        self.assertFalse(is_postfix(demo[3]["results"][0]["TMR"]))
        self.assertFalse(is_postfix(demo[8]["results"][0]["TMR"]))
        self.assertTrue(is_postfix(demo[10]["results"][0]["TMR"]))
        self.assertFalse(is_postfix(demo[11]["results"][0]["TMR"]))