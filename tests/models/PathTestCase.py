from backend.models.graph import Network
from backend.models.path import Path
from backend.models.query import FrameQuery, IdentifierQuery

import unittest


class PathTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")

    def test_path_single_step(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")

        f1["REL1"] = f2

        path = Path().to("REL1")
        results = path.start(f1)

        self.assertTrue(f2 in results)

    def test_path_multiple_steps(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")
        f3 = self.g.register("TEST.FRAME.3")

        f1["REL1"] = f2
        f2["REL2"] = f3

        path = Path().to("REL1").to("REL2")
        results = path.start(f1)

        self.assertTrue(f2 in results)
        self.assertTrue(f3 in results)

    def test_path_recursive_step(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")
        f3 = self.g.register("TEST.FRAME.3")

        f1["REL"] = f2
        f2["REL"] = f3

        path = Path().to("REL", recursive=True)
        results = path.start(f1)

        self.assertTrue(f2 in results)
        self.assertTrue(f3 in results)

    def test_path_recursive_step_with_cycle(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")
        f3 = self.g.register("TEST.FRAME.3")

        f1["REL"] = f2
        f2["REL"] = f3
        f3["REL"] = f1

        path = Path().to("REL", recursive=True)
        results = path.start(f1)

        self.assertTrue(f1 not in results)
        self.assertTrue(f2 in results)
        self.assertTrue(f3 in results)
        self.assertEqual(2, len(results))

    def test_path_step_with_query(self):
        f1 = self.g.register("TEST.FRAME.1")
        f2 = self.g.register("TEST.FRAME.2")
        f3 = self.g.register("TEST.FRAME.3")

        f1["REL"] = [f2, f3]

        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.2", IdentifierQuery.Comparator.EQUALS))
        path = Path().to("REL", query=query)
        results = path.start(f1)

        self.assertTrue(f2 in results)
        self.assertTrue(f3 not in results)