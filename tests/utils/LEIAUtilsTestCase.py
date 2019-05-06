from backend.utils import LEIAUtils
from pkgutil import get_data
from unittest import skip

import unittest
import json


class OntoGenTestCase(unittest.TestCase):

    @staticmethod
    def resource(package, file):
        return json.loads(get_data(package, file).decode('ascii'))

    @skip("Warning: this expects the OntoGen service to be available in order to run correctly.")
    def test_generate_greeting(self):
        greeting_meta = {}
        greeting_tmr = self.resource("tests.resources.tmrs.ontogen", "HiJake.json")

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
