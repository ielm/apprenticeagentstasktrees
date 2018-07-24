from backend.models.agenda import Agenda, Goal
from backend.models.graph import Frame, Graph, Literal
from backend.models.mps import MPRegistry
from backend.models.ontology import Ontology

import unittest


class GoalTestCase(unittest.TestCase):

    def test_status_from_frame(self):
        f = Frame("TEST.1")
        goal = Goal(f)

        f["STATUS"] = "pending"
        self.assertTrue(goal.is_pending())
        self.assertFalse(goal.is_active())
        self.assertFalse(goal.is_abandoned())
        self.assertFalse(goal.is_satisfied())

        f["STATUS"] = "active"
        self.assertFalse(goal.is_pending())
        self.assertTrue(goal.is_active())
        self.assertFalse(goal.is_abandoned())
        self.assertFalse(goal.is_satisfied())

        f["STATUS"] = "abandoned"
        self.assertFalse(goal.is_pending())
        self.assertFalse(goal.is_active())
        self.assertTrue(goal.is_abandoned())
        self.assertFalse(goal.is_satisfied())

        f["STATUS"] = "satisfied"
        self.assertFalse(goal.is_pending())
        self.assertFalse(goal.is_active())
        self.assertFalse(goal.is_abandoned())
        self.assertTrue(goal.is_satisfied())

    def test_status_to_frame(self):
        f = Frame("TEST.1")
        goal = Goal(f)

        goal.status(Goal.Status.PENDING)
        self.assertTrue("pending" in f["STATUS"])
        self.assertFalse("active" in f["STATUS"])
        self.assertFalse("abandoned" in f["STATUS"])
        self.assertFalse("satisfied" in f["STATUS"])

        goal.status(Goal.Status.ACTIVE)
        self.assertFalse("pending" in f["STATUS"])
        self.assertTrue("active" in f["STATUS"])
        self.assertFalse("abandoned" in f["STATUS"])
        self.assertFalse("satisfied" in f["STATUS"])

        goal.status(Goal.Status.ABANDONED)
        self.assertFalse("pending" in f["STATUS"])
        self.assertFalse("active" in f["STATUS"])
        self.assertTrue("abandoned" in f["STATUS"])
        self.assertFalse("satisfied" in f["STATUS"])

        goal.status(Goal.Status.SATISFIED)
        self.assertFalse("pending" in f["STATUS"])
        self.assertFalse("active" in f["STATUS"])
        self.assertFalse("abandoned" in f["STATUS"])
        self.assertTrue("satisfied" in f["STATUS"])

    def test_assess(self):
        graph = Graph("TEST")
        f1 = graph.register("GOAL.1")
        f2 = graph.register("OBJECT.1")
        f3 = graph.register("COLOR.1")

        f1["GOAL-STATE"] = f3
        f3["DOMAIN"] = f2
        f3["RANGE"] = "yellow"

        goal = Goal(f1)
        self.assertFalse(goal.is_satisfied())

        f2["COLOR"] = "yellow"
        goal.assess()
        self.assertTrue(goal.is_satisfied())

    def test_subgoals(self):
        graph = Graph("TEST")
        f1 = graph.register("GOAL.1")
        f2 = graph.register("GOAL.2")
        f3 = graph.register("GOAL.3")

        f1["HAS-GOAL"] = [f2, f3]

        goal = Goal(f1)
        subgoals = goal.subgoals()
        subgoals = list(map(lambda subgoal: subgoal.frame, subgoals))
        self.assertTrue(f2 in subgoals)
        self.assertTrue(f3 in subgoals)

    def test_prioritize(self):

        def priority_calculation(agent):
            return 0.5

        MPRegistry[priority_calculation.__name__] = priority_calculation

        graph = Graph("TEST")
        f1 = graph.register("GOAL.1")
        f2 = graph.register("MEANING-PROCEDURE.1")

        f1["PRIORITY-CALCULATION"] = f2
        f2["CALLS"] = Literal(priority_calculation.__name__)

        self.assertEqual(0, len(f1["PRIORITY"]))

        goal = Goal(f1)
        goal.prioritize(None)
        self.assertTrue(f1["PRIORITY"] == 0.5)

    def test_priority(self):
        graph = Graph("TEST")
        f1 = graph.register("GOAL.1")

        goal = Goal(f1)
        self.assertEqual(0.0, goal.priority())

        f1["PRIORITY"] = 0.5
        self.assertEqual(0.5, goal.priority())

    def test_pursue(self):
        def select_action(agent):
            return Frame("IDLE.1")  # Properties can be added here

        MPRegistry[select_action.__name__] = select_action

        graph = Graph("TEST")
        f1 = graph.register("GOAL.1")
        f2 = graph.register("MEANING-PROCEDURE.1")

        f1["ACTION-SELECTION"] = f2
        f2["CALLS"] = Literal(select_action.__name__)

        goal = Goal(f1)

        action = goal.pursue(None)
        self.assertEqual("IDLE.1", action.frame.name())