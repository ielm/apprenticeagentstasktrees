from backend.models.path import Path
# from backend.models.query import FrameQuery, IdentifierQuery
from backend.models.view import View
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Query import IdComparator, Query
from ontograph.Space import Space

import unittest


class ViewTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        self.agent = None
        self.space = Space("TEST")

    def test_view_no_modifiers(self):
        f = Frame("@TEST.FRAME.1")
        f["SLOT"] = 123

        v = View(self.agent, self.space).view()
        self.assertEqual(1, len(v))
        self.assertEqual(f["SLOT"], list(v)[0]["SLOT"])

    def test_view_query(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")

        query = Query().search(IdComparator("@TEST.FRAME.1"))

        v = View(self.agent, self.space, query=query).view()
        self.assertEqual(1, len(v))
        self.assertTrue("@TEST.FRAME.1" in v)
        self.assertTrue("@TEST.FRAME.2" not in v)

    def test_view_query_removes_relations(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")

        f1["REL1"] = f1
        f1["REL2"] = f2

        query = Query().search(IdComparator("@TEST.FRAME.1"))

        self.assertEqual(2, len(self.space))
        self.assertTrue("@TEST.FRAME.1" in self.space)
        self.assertTrue("@TEST.FRAME.2" in self.space)
        self.assertTrue("REL1" in Frame("@TEST.FRAME.1"))
        self.assertTrue("REL2" in Frame("@TEST.FRAME.1"))

        v = View(self.agent, self.space, query=query).view()

        self.assertEqual(1, len(v))
        self.assertTrue("@TEST.FRAME.1" in v)
        self.assertTrue("@TEST.FRAME.2" not in v)
        self.assertTrue("REL1" in list(v)[0])
        self.assertTrue("REL2" not in list(v)[0])

    def test_view_query_maintains_full_identifiers(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")

        f1["REL1"] = f1
        f1["REL2"] = Frame("@SOME.OTHER.1")

        query = Query().search(IdComparator("@TEST.FRAME.1"))

        v = View(self.agent, self.space, query=query).view()
        self.assertEqual(v.name, "TEST")
        self.assertTrue(list(v)[0]["REL1"] == "@TEST.FRAME.1")
        self.assertTrue(list(v)[0]["REL2"] == "@SOME.OTHER.1")

    def test_view_query_follows_path(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")

        f1["REL1"] = f2

        query = Query().search(IdComparator("@TEST.FRAME.1"))
        path = Path().to("REL1")

        v = View(self.agent, self.space, query=query, follow=path).view()
        self.assertTrue("@TEST.FRAME.1" in v)
        self.assertTrue("@TEST.FRAME.2" in v)

    def test_view_query_follows_multiple_paths(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")
        f3 = Frame("@TEST.FRAME.3")

        f1["REL1"] = f2
        f1["REL2"] = f3

        query = Query().search(IdComparator("@TEST.FRAME.1"))
        path1 = Path().to("REL1")
        path2 = Path().to("REL2")

        v = View(self.agent, self.space, query=query, follow=[path1, path2]).view()
        self.assertTrue("@TEST.FRAME.1" in v)
        self.assertTrue("@TEST.FRAME.2" in v)
        self.assertTrue("@TEST.FRAME.3" in v)

    def test_view_query_follows_multi_step_path(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")
        f3 = Frame("@TEST.FRAME.3")

        f1["REL1"] = f2
        f2["REL2"] = f3

        query = Query().search(IdComparator("@TEST.FRAME.1"))
        path = Path().to("REL1").to("REL2")

        v = View(self.agent, self.space, query=query, follow=path).view()
        self.assertTrue("@TEST.FRAME.1" in v)
        self.assertTrue("@TEST.FRAME.2" in v)
        self.assertTrue("@TEST.FRAME.3" in v)

    def test_view_query_follows_recursive_path(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")
        f3 = Frame("@TEST.FRAME.3")

        f1["REL"] = f2
        f2["REL"] = f3

        query = Query().search(IdComparator("@TEST.FRAME.1"))
        path = Path().to("REL", recursive=True)

        v = View(self.agent, self.space, query=query, follow=path).view()
        self.assertTrue("@TEST.FRAME.1" in v)
        self.assertTrue("@TEST.FRAME.2" in v)
        self.assertTrue("@TEST.FRAME.3" in v)

    def test_view_query_follows_recursive_path_with_cycles(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")
        f3 = Frame("@TEST.FRAME.3")

        f1["REL"] = f2
        f2["REL"] = f3
        f3["REL"] = f1

        query = Query().search(IdComparator("@TEST.FRAME.1"))
        path = Path().to("REL", recursive=True)

        v = View(self.agent, self.space, query=query, follow=path).view()
        self.assertTrue("@TEST.FRAME.1" in v)
        self.assertTrue("@TEST.FRAME.2" in v)
        self.assertTrue("@TEST.FRAME.3" in v)
        self.assertEqual(3, len(v))

    def test_view_query_follows_path_with_inner_query(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")
        f3 = Frame("@TEST.FRAME.3")

        f1["REL"] = [f2, f3]

        query = Query().search(IdComparator("@TEST.FRAME.1"))
        inner_query = IdComparator("@TEST.FRAME.2")
        path = Path().to("REL", comparator=inner_query)

        v = View(self.agent, self.space, query=query, follow=path).view()
        self.assertTrue("@TEST.FRAME.1" in v)
        self.assertTrue("@TEST.FRAME.2" in v)
        self.assertTrue("@TEST.FRAME.3" not in v)

    def test_view_query_follows_paths_and_updates_relations_with_absolute_identifiers(self):
        all = Frame("@ONT.ALL")
        thing = Frame("@ONT.THING").add_parent("@ONT.ALL")

        self.assertEqual(thing["IS-A"][0], all)

        f = Frame("@TEST.FRAME.1").add_parent("@ONT.THING")

        path = Path().to("*").to("*")
        v = View(self.agent, self.space, follow=path).view()

        vf = list(filter(lambda frame: frame.id == "@ONT.THING", v))[0]
        self.assertEqual(vf["IS-A"][0], "@ONT.ALL")