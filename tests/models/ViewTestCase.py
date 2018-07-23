from backend.models.graph import Network
from backend.models.path import Path
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

    def test_view_query_follows_path(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")

        f1["REL1"] = f2

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))
        path = Path().to("REL1")

        v = View(self.n, self.g, query=query, follow=path).view()
        self.assertTrue("TEST.FRAME.1" in v)
        self.assertTrue("TEST.FRAME.2" in v)

    def test_view_query_follows_multiple_paths(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")
        f3 = self.g.register("TEST.FRAME.3")

        f1["REL1"] = f2
        f1["REL2"] = f3

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))
        path1 = Path().to("REL1")
        path2 = Path().to("REL2")

        v = View(self.n, self.g, query=query, follow=[path1, path2]).view()
        self.assertTrue("TEST.FRAME.1" in v)
        self.assertTrue("TEST.FRAME.2" in v)
        self.assertTrue("TEST.FRAME.3" in v)

    def test_view_query_follows_multi_step_path(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")
        f3 = self.g.register("TEST.FRAME.3")

        f1["REL1"] = f2
        f2["REL2"] = f3

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))
        path = Path().to("REL1").to("REL2")

        v = View(self.n, self.g, query=query, follow=path).view()
        self.assertTrue("TEST.FRAME.1" in v)
        self.assertTrue("TEST.FRAME.2" in v)
        self.assertTrue("TEST.FRAME.3" in v)

    def test_view_query_follows_recursive_path(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")
        f3 = self.g.register("TEST.FRAME.3")

        f1["REL"] = f2
        f2["REL"] = f3

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))
        path = Path().to("REL", recursive=True)

        v = View(self.n, self.g, query=query, follow=path).view()
        self.assertTrue("TEST.FRAME.1" in v)
        self.assertTrue("TEST.FRAME.2" in v)
        self.assertTrue("TEST.FRAME.3" in v)

    def test_view_query_follows_recursive_path_with_cycles(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")
        f3 = self.g.register("TEST.FRAME.3")

        f1["REL"] = f2
        f2["REL"] = f3
        f3["REL"] = f1

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))
        path = Path().to("REL", recursive=True)

        v = View(self.n, self.g, query=query, follow=path).view()
        self.assertTrue("TEST.FRAME.1" in v)
        self.assertTrue("TEST.FRAME.2" in v)
        self.assertTrue("TEST.FRAME.3" in v)
        self.assertEqual(3, len(v))

    def test_view_query_follows_path_with_inner_query(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")
        f3 = self.g.register("TEST.FRAME.3")

        f1["REL"] = [f2, f3]

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))
        inner_query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.2", IdentifierQuery.Comparator.EQUALS))
        path = Path().to("REL", query=inner_query)

        v = View(self.n, self.g, query=query, follow=path).view()
        self.assertTrue("TEST.FRAME.1" in v)
        self.assertTrue("TEST.FRAME.2" in v)
        self.assertTrue("TEST.FRAME.3" not in v)

    def test_view_query_follows_paths_and_updates_relations_with_absolute_identifiers(self):
        ont = self.n.register("ONT")
        all = ont.register("ALL")
        thing = ont.register("THING", isa="ALL")

        self.assertIsNone(thing["IS-A"][0]._value.graph)
        self.assertEqual(thing["IS-A"][0].resolve(), all)

        f = self.g.register("TEST.FRAME.1", isa="ONT.THING")

        path = Path().to("*").to("*")
        v = View(self.n, self.g, follow=path).view()

        self.assertEqual(v["ONT.THING"]["IS-A"][0]._value.graph, "ONT")