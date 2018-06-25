from backend.models.graph import Graph, Network
from backend.models.query import FrameQuery, IdentifierQuery
from backend.models.view import View

import unittest


class ViewTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")

    def test_view_no_modifiers(self):
        f = self.g.register("TEST.FRAME.1")
        f["SLOT"] = 123

        v = View(self.n, self.g).view()
        self.assertEqual(1, len(v))
        self.assertEqual(f["SLOT"], v[f._identifier]["SLOT"])

    def test_view_query(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))

        v = View(self.n, self.g, query=query).view()
        self.assertEqual(1, len(v))
        self.assertTrue("TEST.FRAME.1" in v)
        self.assertTrue("TEST.FRAME.2" not in v)

    def test_view_query_removes_relations(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")

        f1["REL1"] = f1
        f1["REL2"] = f2

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))

        v = View(self.n, self.g, query=query).view()
        self.assertEqual(1, len(v))
        self.assertTrue("TEST.FRAME.1" in v)
        self.assertTrue("TEST.FRAME.2" not in v)
        self.assertTrue("REL1" in v["TEST.FRAME.1"])
        self.assertTrue("REL2" not in v["TEST.FRAME.1"])

        self.assertEqual(2, len(self.g))
        self.assertTrue("TEST.FRAME.1" in self.g)
        self.assertTrue("TEST.FRAME.2" in self.g)
        self.assertTrue("REL1" in self.g["TEST.FRAME.1"])
        self.assertTrue("REL2" in self.g["TEST.FRAME.1"])

    def test_view_query_maintains_full_identifiers(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")

        f1["REL1"] = f1
        f1["REL2"] = "SOME.OTHER.1"

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))

        v = View(self.n, self.g, query=query).view()
        self.assertEqual(v._namespace, "TEST")
        self.assertTrue(v["TEST.FRAME.1"]["REL1"] == "TEST.FRAME.1")
        self.assertTrue(v["TEST.FRAME.1"]["REL2"] == "SOME.OTHER.1")