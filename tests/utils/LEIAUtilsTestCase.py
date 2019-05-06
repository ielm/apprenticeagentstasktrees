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
        file = os.path.abspath(__package__) + "/../resources/tmrs/HiJake.json"
        greeting_tmr = self.resource(file)

        output = LEIAUtils.ontogen_generate(greeting_tmr, greeting_meta)

        self.assertEqual(output.text, "Hi, Jake")
