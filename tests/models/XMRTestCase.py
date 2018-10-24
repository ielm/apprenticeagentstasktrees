from backend.models.graph import Frame, Literal, Network
from backend.models.xmr import XMR

import unittest


class XMRTestCase(unittest.TestCase):

    def test_status(self):
        frame = Frame("TEST")
        frame["STATUS"] = XMR.Status.RECEIVED

        self.assertEqual(XMR.Status.RECEIVED, XMR(frame).status())

    def test_type(self):
        frame = Frame("TEST")
        frame["TYPE"] = XMR.Type.LANGUAGE

        self.assertEqual(XMR.Type.LANGUAGE, XMR(frame).type())

    def test_source(self):
        n = Network()
        g = n.register("TEST")
        source = g.register("SOURCE")

        frame = g.register("XMR")
        frame["SOURCE"] = source

        self.assertEqual(source, XMR(frame).source())

    def test_graph(self):
        n = Network()
        g = n.register("TEST")
        f = g.register("XMR")
        f["REFERS-TO-GRAPH"] = Literal(g._namespace)

        self.assertEqual(g, XMR(f).graph(n))