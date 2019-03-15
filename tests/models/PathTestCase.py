from backend.models.path import Path
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Query import IdComparator

import unittest


class PathTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_path_single_step(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")

        f1["REL1"] = f2

        path = Path().to("REL1")
        results = path.start(f1)

        self.assertTrue(f2 in results)

    def test_path_single_step_with_wildcard(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")

        f1["REL1"] = f2

        path = Path().to("*")
        results = path.start(f1)

        self.assertTrue(f2 in results)

    def test_path_multiple_steps(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")
        f3 = Frame("@TEST.FRAME.3")

        f1["REL1"] = f2
        f2["REL2"] = f3

        path = Path().to("REL1").to("REL2")
        results = path.start(f1)

        self.assertTrue(f2 in results)
        self.assertTrue(f3 in results)

    def test_path_recursive_step(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")
        f3 = Frame("@TEST.FRAME.3")

        f1["REL"] = f2
        f2["REL"] = f3

        path = Path().to("REL", recursive=True)
        results = path.start(f1)

        self.assertTrue(f2 in results)
        self.assertTrue(f3 in results)

    def test_path_recursive_step_with_cycle(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")
        f3 = Frame("@TEST.FRAME.3")

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
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")
        f3 = Frame("@TEST.FRAME.3")

        f1["REL"] = [f2, f3]

        comparator = IdComparator("@TEST.FRAME.2")
        path = Path().to("REL", comparator=comparator)
        results = path.start(f1)

        self.assertTrue(f2 in results)
        self.assertTrue(f3 not in results)