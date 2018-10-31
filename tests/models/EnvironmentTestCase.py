from backend.models.environment import Environment
from backend.models.graph import Frame, Network

import unittest


class EnvironmentTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("ENV")
        self.g.register("EPOCH")

    def test_advance(self):
        self.assertEqual(1, len(self.g.search(Frame.q(self.n).isa("ENV.EPOCH"))))

        env = Environment(self.g)

        env.advance()
        self.assertEqual(2, len(self.g.search(Frame.q(self.n).isa("ENV.EPOCH"))))
        self.assertEqual(1, self.g["ENV.EPOCH.1"]["TIME"].singleton())
        self.assertNotIn("FOLLOWS", self.g["ENV.EPOCH.1"])

        env.advance()
        self.assertEqual(3, len(self.g.search(Frame.q(self.n).isa("ENV.EPOCH"))))
        self.assertEqual(2, self.g["ENV.EPOCH.2"]["TIME"].singleton())
        self.assertTrue(self.g["ENV.EPOCH.2"]["FOLLOWS"] == self.g["ENV.EPOCH.1"])


    def test_history(self):
        env = Environment(self.g)

        env.advance()
        env.advance()
        env.advance()

        history = env.history()
        self.assertEqual([self.g["EPOCH.1"], self.g["EPOCH.2"], self.g["EPOCH.3"]], history)

    def test_enter(self):
        env = Environment(self.g)
        obj = self.g.register("TEST")

        env.advance()
        env.advance()

        # 1) The object is only added to the most recent epoch
        env.enter(obj)
        self.assertNotIn(obj, self.g["EPOCH.1"]["CONTAINS"])
        self.assertIn(obj, self.g["EPOCH.2"]["CONTAINS"])

        # 2) Objects in the most recent epoch are carried into the next epoch
        env.advance()
        self.assertNotIn(obj, self.g["EPOCH.1"]["CONTAINS"])
        self.assertIn(obj, self.g["EPOCH.2"]["CONTAINS"])
        self.assertIn(obj, self.g["EPOCH.3"]["CONTAINS"])

        # 3) Objects already in an epoch are not added twice (it becomes a no-op)
        env.enter(obj)
        self.assertNotIn(obj, self.g["EPOCH.1"]["CONTAINS"])
        self.assertIn(obj, self.g["EPOCH.2"]["CONTAINS"])
        self.assertIn(obj, self.g["EPOCH.3"]["CONTAINS"])
        self.assertEqual(1, len(self.g["EPOCH.2"]["CONTAINS"]))
        self.assertEqual(1, len(self.g["EPOCH.3"]["CONTAINS"]))

    def test_exit(self):
        env = Environment(self.g)
        obj = self.g.register("TEST")

        env.advance()
        env.enter(obj)
        env.advance()

        # 1) The object is only removed from the most recent epoch
        env.exit(obj)
        self.assertIn(obj, self.g["EPOCH.1"]["CONTAINS"])
        self.assertNotIn(obj, self.g["EPOCH.2"]["CONTAINS"])

        # 2) Objects not in the most recent epoch are not carried into the next epoch
        env.advance()
        self.assertIn(obj, self.g["EPOCH.1"]["CONTAINS"])
        self.assertNotIn(obj, self.g["EPOCH.2"]["CONTAINS"])
        self.assertNotIn(obj, self.g["EPOCH.3"]["CONTAINS"])

        # 3) Objects not in an epoch cannot be removed (it becomes a no-op)
        env.exit(obj)
        self.assertIn(obj, self.g["EPOCH.1"]["CONTAINS"])
        self.assertNotIn(obj, self.g["EPOCH.2"]["CONTAINS"])
        self.assertNotIn(obj, self.g["EPOCH.3"]["CONTAINS"])

    def test_view(self):
        env = Environment(self.g)
        obj1 = self.g.register("TEST.1")
        obj2 = self.g.register("TEST.2")

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

        self.assertEqual(env.view(0), env.view("ENV.EPOCH.1"))
        self.assertEqual(env.view(1), env.view(self.g["ENV.EPOCH.2"]))

    def test_current(self):
        env = Environment(self.g)
        obj1 = self.g.register("TEST.1")
        obj2 = self.g.register("TEST.2")

        env.advance()
        env.enter(obj1)
        env.advance()
        env.enter(obj2)

        self.assertEqual(env.view(1), env.current())