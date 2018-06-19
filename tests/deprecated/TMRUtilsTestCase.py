from models.tmr import TMR
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase

from unittest import skip


@DeprecationWarning
class TaskModelTestCase(ApprenticeAgentsTestCase):

    @skip
    def test_is_utterance(self):
        demo = self.resource('resources/DemoMay2018_Analyses.json')

        self.assertTrue(TMR(demo[0]).is_utterance())
        self.assertTrue(TMR(demo[1]).is_utterance())
        self.assertTrue(TMR(demo[3]).is_utterance())
        self.assertTrue(TMR(demo[10]).is_utterance())
        self.assertTrue(TMR(demo[11]).is_utterance())
        self.assertTrue(TMR(demo[18]).is_utterance())
        self.assertTrue(TMR(demo[38]).is_utterance())

        self.assertFalse(TMR(demo[2]).is_utterance())
        self.assertFalse(TMR(demo[4]).is_utterance())
        self.assertFalse(TMR(demo[5]).is_utterance())
        self.assertFalse(TMR(demo[6]).is_utterance())
        self.assertFalse(TMR(demo[7]).is_utterance())
        self.assertFalse(TMR(demo[8]).is_utterance())
        self.assertFalse(TMR(demo[9]).is_utterance())
        self.assertFalse(TMR(demo[12]).is_utterance())
        self.assertFalse(TMR(demo[13]).is_utterance())
        self.assertFalse(TMR(demo[14]).is_utterance())
        self.assertFalse(TMR(demo[15]).is_utterance())
        self.assertFalse(TMR(demo[16]).is_utterance())
        self.assertFalse(TMR(demo[17]).is_utterance())

    @skip
    def test_find_themes(self):
        demo = self.resource('resources/DemoMay2018_Analyses.json')

        self.assertEqual(TMR(demo[0]).find_themes(), ["CHAIR"])
        self.assertEqual(TMR(demo[2]).find_themes(), ["TAKE", "SCREWDRIVER"])

    @skip
    def test_is_postfix(self):
        demo = self.resource('resources/DemoMay2018_Analyses.json')

        self.assertFalse(TMR(demo[0]).is_postfix())
        self.assertFalse(TMR(demo[1]).is_postfix())
        self.assertFalse(TMR(demo[3]).is_postfix())
        self.assertFalse(TMR(demo[8]).is_postfix())
        self.assertTrue(TMR(demo[10]).is_postfix())
        self.assertFalse(TMR(demo[11]).is_postfix())
        self.assertTrue(TMR(demo[38]).is_postfix())

    @skip
    def test_find_main_event(self):
        demo = self.resource('resources/DemoMay2018_Analyses.json')

        self.assertEqual("POSSESSION-EVENT", TMR(demo[1]).find_main_event().concept)

    @skip
    def test_convert_ontological_types(self):
        demo = self.resource('resources/DemoMay2018_Analyses.json')

        tmr = TMR(demo[10])  # We have assembled a front leg.

        self.assertEqual({"ARTIFACT-LEG-12", "ASPECT-12", "SET-12", "BUILD-12X"}, set(tmr.keys()))
        self.assertEqual(["BUILD-12X"], tmr["ARTIFACT-LEG-12"]["THEME-OF"])
        self.assertEqual(["BUILD-12X"], tmr["ASPECT-12"]["SCOPE"])
        self.assertEqual(["BUILD-12X"], tmr["SET-12"]["AGENT-OF"])

        self.assertEqual("BUILD", tmr["BUILD-12X"].concept)
