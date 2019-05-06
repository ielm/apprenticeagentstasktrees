from backend.utils import LEIAUtils
from ontograph import graph
from backend.models.tmr import TMR

import unittest
import json
import os


class OntoGenTestCase(unittest.TestCase):

    @staticmethod
    def resource(fp):
        r = None
        with open(fp) as f:
            r = json.load(f)
        return r

    def test_generate_greeting(self):
        greeting_meta = {}
        file = os.path.abspath(__package__) + "/../resources/tmrs/ontogen/HiJake.json"
        greeting_tmr = self.resource(file)

        output = LEIAUtils.ontogen_generate(greeting_tmr, greeting_meta)

        self.assertEqual(output.text, "Hi, Jake")

    # def test_generate_explanation(self):
    #     #     explanation_meta = {
    #     #         "FORMAT": "DIRECTED",
    #     #         "TENSE": "PRESENT"
    #     #     }
    #     #     file = os.path.abspath(__package__) + "/../resources/tmrs/ontogen/GettingScrewdriver.json"
    #     #     explanation_tmr = self.resource(file)
    #     #
    #     #     out = LEIAUtils.ontogen_generate(explanation_tmr, explanation_meta)
    #     #     self.assertEqual(out.text, "I am carrying the screwdriver.")
