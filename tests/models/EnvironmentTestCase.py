from backend.models.environment import Environment

from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Query import IsAComparator, Query
from ontograph.Space import Space

import unittest


class EnvironmentTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

        Frame("@ENV.EPOCH")
        Frame("@ONT.LOCATION")

    def test_advance(self):
        self.assertEqual(1, len(Query().search(IsAComparator("@ENV.EPOCH")).start(graph)))

        env = Environment(Space("ENV"))

        env.advance()
        self.assertEqual(2, len(Query().search(IsAComparator("@ENV.EPOCH")).start(graph)))
        self.assertEqual(1, Frame("@ENV.EPOCH.1")["TIME"].singleton())
        self.assertNotIn("FOLLOWS", Frame("@ENV.EPOCH.1"))

        env.advance()
        self.assertEqual(3, len(Query().search(IsAComparator("@ENV.EPOCH")).start(graph)))
        self.assertEqual(2, Frame("@ENV.EPOCH.2")["TIME"].singleton())
        self.assertEqual(Frame("@ENV.EPOCH.1"), Frame("@ENV.EPOCH.2")["FOLLOWS"])

    def test_history(self):
        env = Environment(Space("ENV"))

        env.advance()
        env.advance()
        env.advance()

        history = env.history()
        self.assertEqual([Frame("@ENV.EPOCH.1"), Frame("@ENV.EPOCH.2"), Frame("@ENV.EPOCH.3")], history)

    def test_enter(self):
        env = Environment(Space("ENV"))
        obj = Frame("@ENV.TEST")

        env.advance()
        env.advance()

        # 1) The object is only added to the most recent epoch
        env.enter(obj)
        self.assertNotIn(obj, Frame("@ENV.EPOCH.1")["CONTAINS"])
        self.assertIn(obj, Frame("@ENV.EPOCH.2")["CONTAINS"])

        # 2) Objects in the most recent epoch are carried into the next epoch
        env.advance()
        self.assertNotIn(obj, Frame("@ENV.EPOCH.1")["CONTAINS"])
        self.assertIn(obj, Frame("@ENV.EPOCH.2")["CONTAINS"])
        self.assertIn(obj, Frame("@ENV.EPOCH.3")["CONTAINS"])

        # 3) Objects already in an epoch are not added twice (it becomes a no-op)
        env.enter(obj)
        self.assertNotIn(obj, Frame("@ENV.EPOCH.1")["CONTAINS"])
        self.assertIn(obj, Frame("@ENV.EPOCH.2")["CONTAINS"])
        self.assertIn(obj, Frame("@ENV.EPOCH.3")["CONTAINS"])
        self.assertEqual(1, len(Frame("@ENV.EPOCH.2")["CONTAINS"]))
        self.assertEqual(1, len(Frame("@ENV.EPOCH.3")["CONTAINS"]))

    def test_exit(self):
        env = Environment(Space("ENV"))
        obj = Frame("@ENV.TEST")

        env.advance()
        env.enter(obj)
        env.advance()

        # 1) The object is only removed from the most recent epoch
        env.exit(obj)
        self.assertIn(obj, Frame("@ENV.EPOCH.1")["CONTAINS"])
        self.assertNotIn(obj, Frame("@ENV.EPOCH.2")["CONTAINS"])

        # 2) Objects not in the most recent epoch are not carried into the next epoch
        env.advance()
        self.assertIn(obj, Frame("@ENV.EPOCH.1")["CONTAINS"])
        self.assertNotIn(obj, Frame("@ENV.EPOCH.2")["CONTAINS"])
        self.assertNotIn(obj, Frame("@ENV.EPOCH.3")["CONTAINS"])

        # 3) Objects not in an epoch cannot be removed (it becomes a no-op)
        env.exit(obj)
        self.assertIn(obj, Frame("@ENV.EPOCH.1")["CONTAINS"])
        self.assertNotIn(obj, Frame("@ENV.EPOCH.2")["CONTAINS"])
        self.assertNotIn(obj, Frame("@ENV.EPOCH.3")["CONTAINS"])

    def test_move(self):
        env = Environment(Space("ENV"))
        obj = Frame("@ENV.TEST")

        loc1 = Frame("@ENV.LOCATION.?")
        loc2 = Frame("@ENV.LOCATION.?")

        env.advance()
        env.enter(obj)

        # 1) Objects default to distance 1.0, but can be moved to arbitrary locations
        self.assertEqual(Frame("@ONT.LOCATION"), env.location(obj))
        env.move(obj, loc1)
        self.assertEqual(loc1, env.location(obj))

        # 2) Objects retain their location over time
        env.advance()
        self.assertEqual(loc1, env.location(obj))

        # 3) Objects can be moved multiple times; this will not affect previous epochs
        env.move(obj, loc2)
        self.assertEqual(loc2, env.location(obj))
        self.assertEqual(loc1, env.location(obj, epoch=0))

        # 4) Objects can enter at specific locations
        obj2 = Frame("@ENV.TEST2")
        env.enter(obj2, location=loc1)
        self.assertEqual(loc1, env.location(obj2))

    def test_view(self):
        env = Environment(Space("ENV"))
        obj1 = Frame("@ENV.TEST.?")
        obj2 = Frame("@ENV.TEST.?")

        env.advance()
        env.enter(obj1)
        env.advance()
        env.enter(obj2)

        view = env.view(0)
        self.assertIn(obj1, view)
        self.assertNotIn(obj2, view)

        view = env.view(1)
        self.assertIn(obj1, view)
        self.assertIn(obj2, view)

        self.assertEqual(env.view(0), env.view("@ENV.EPOCH.1"))
        self.assertEqual(env.view(1), env.view(Frame("@ENV.EPOCH.2")))

    def test_current(self):
        env = Environment(Space("ENV"))
        obj1 = Frame("@ENV.TEST.?")
        obj2 = Frame("@ENV.TEST.?")

        env.advance()
        env.enter(obj1)
        env.advance()
        env.enter(obj2)

        self.assertEqual(env.view(1), env.current())