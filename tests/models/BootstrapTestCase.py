from backend.models.bootstrap import BootstrapKnowledge
from backend.models.graph import Literal, Network

import unittest


class BootstrapKnowledgeTestCase(unittest.TestCase):

    def test_call(self):
        n = Network()
        g = n.register("TEST")
        f = g.register("SOMEFRAME")

        boot = BootstrapKnowledge(n, "TEST.SOMEFRAME", "slot", Literal(123))
        boot()

        self.assertTrue(123 in f["slot"])