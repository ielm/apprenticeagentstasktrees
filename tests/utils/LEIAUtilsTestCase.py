from backend.models.tmr import TMR
from backend.models.xmr import XMR
from backend.utils import LEIAUtils
from ontograph import graph
from ontograph.Space import Space
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

        graph.load(greeting_tmr)
        xmr = XMR.instance(Space("OUTPUTS"), "OUT", XMR.Signal.OUTPUT, XMR.Type.LANGUAGE, XMR.OutputStatus.PENDING, "@SELF.ROBOT.1", "@OUTPUTS.TMR.1")
        output = LEIAUtils.ontogen_generate(TMR(xmr.frame), greeting_meta)

        self.assertEqual(output, "Hi, Jake")

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
