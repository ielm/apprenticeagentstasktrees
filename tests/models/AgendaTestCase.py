from backend.models.agenda import Action, Agenda, Condition, Goal
from backend.models.graph import Frame, Graph, Literal
from backend.models.mps import MPRegistry
from backend.models.ontology import Ontology

import unittest


class AgendaTestCase(unittest.TestCase):

    def test_goals(self):
        graph = Graph("TEST")
        f1 = graph.register("AGENDA.1")  # Typically the agent identity frame (so, e.g., ROBOT.1) is used, as there is no "AGENDA".
        g1 = graph.register("GOAL.1")
        g2 = graph.register("GOAL.2")
        g3 = graph.register("GOAL.3")
        g4 = graph.register("GOAL.4")

        f1["GOAL"] = [g1, g2, g3, g4]

        g1["STATUS"] = "pending"
        g2["STATUS"] = "active"
        g3["STATUS"] = "abandoned"
        g4["STATUS"] = "satisfied"

        agenda = Agenda(f1)
        self.assertEqual(agenda.goals(), [Goal(g2)])
        self.assertEqual(agenda.goals(pending=True), [Goal(g1), Goal(g2)])
        self.assertEqual(agenda.goals(active=False), [])
        self.assertEqual(agenda.goals(abandoned=True, active=False), [Goal(g3)])
        self.assertEqual(agenda.goals(satisfied=True, active=False), [Goal(g4)])

    def test_add_goal(self):
        graph = Graph("TEST")
        f1 = graph.register("AGENDA.1")
        g1 = graph.register("GOAL.1")
        g2 = graph.register("GOAL.2")

        agenda = Agenda(f1)
        agenda.add_goal(g1)
        agenda.add_goal(Goal(g2))

        self.assertEqual(agenda.goals(pending=True), [Goal(g1), Goal(g2)])

    def test_prepare_action(self):
        graph = Graph("TEST")
        f1 = graph.register("AGENDA.1")
        a1 = graph.register("ACTION.1")
        a2 = graph.register("ACTION.2")

        agenda = Agenda(f1)

        agenda.prepare_action(a1)
        self.assertEqual(len(f1["ACTION-TO-TAKE"]), 1)
        self.assertEqual(f1["ACTION-TO-TAKE"][0].resolve(), a1)

        agenda.prepare_action(Action(a2))
        self.assertEqual(len(f1["ACTION-TO-TAKE"]), 1)
        self.assertEqual(f1["ACTION-TO-TAKE"][0].resolve(), a2)

    def test_action(self):
        graph = Graph("TEST")
        f1 = graph.register("AGENDA.1")
        a1 = graph.register("ACTION.1")

        f1["ACTION-TO-TAKE"] = a1

        agenda = Agenda(f1)
        self.assertEqual(a1, agenda.action())
        self.assertEqual(Action, agenda.action().__class__)


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

    # def test_assess(self):
    #     graph = Graph("TEST")
    #     f1 = graph.register("GOAL.1")
    #     f2 = graph.register("OBJECT.1")
    #     f3 = graph.register("COLOR.1")
    #
    #     f1["GOAL-STATE"] = f3
    #     f3["DOMAIN"] = f2
    #     f3["RANGE"] = "yellow"
    #
    #     goal = Goal(f1)
    #     self.assertFalse(goal.is_satisfied())
    #
    #     f2["COLOR"] = "yellow"
    #     goal.assess()
    #     self.assertTrue(goal.is_satisfied())

    def test_conditions(self):
        graph = Graph("TEST")
        g = graph.register("GOAL.1")
        gc = graph.register("GOAL-CONDITION.1")

        g["ON-CONDITION"] = gc

        goal = Goal(g)
        self.assertEqual(goal.conditions(), [Condition(gc)])
        self.assertEqual(goal.conditions()[0].frame, gc)
        self.assertIsInstance(goal.conditions()[0].frame, Frame)

    def test_assess(self):
        graph = Graph("TEST")
        g = graph.register("GOAL.1")
        gc = graph.register("GOAL-CONDITION.1")
        wc = graph.register("COLOR.1")
        obj = graph.register("OBJECT.1")

        g["ON-CONDITION"] = gc
        g["STATUS"] = Literal(Goal.Status.ACTIVE.name)
        gc["WITH-CONDITION"] = wc
        gc["APPLY-STATUS"] = Literal(Goal.Status.SATISFIED.name)
        wc["DOMAIN"] = obj
        wc["RANGE"] = "yellow"

        goal = Goal(g)
        self.assertTrue(goal.is_active())

        goal.assess()
        self.assertTrue(goal.is_active())

        obj["COLOR"] = "yellow"
        goal.assess()
        self.assertTrue(goal.is_satisfied())

    def test_assess_multiple_conditions(self):
        graph = Graph("TEST")
        g = graph.register("GOAL.1")
        gc1 = graph.register("GOAL-CONDITION.1")
        gc2 = graph.register("GOAL-CONDITION.2")
        wc = graph.register("COLOR.1")
        obj = graph.register("OBJECT.1")

        g["ON-CONDITION"] = [gc1, gc2]
        g["STATUS"] = Literal(Goal.Status.ACTIVE.name)
        gc1["WITH-CONDITION"] = wc
        gc1["APPLY-STATUS"] = Literal(Goal.Status.SATISFIED.name)
        gc1["ORDER"] = 2
        gc2["WITH-CONDITION"] = wc
        gc2["APPLY-STATUS"] = Literal(Goal.Status.ABANDONED.name)
        gc2["ORDER"] = 1
        wc["DOMAIN"] = obj
        wc["RANGE"] = "yellow"
        obj["COLOR"] = "yellow"

        goal = Goal(g)
        goal.assess()
        self.assertTrue(goal.is_abandoned())

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
        self.assertIsInstance(subgoals[0], Frame)

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

    def test_inherits_non_instanced_priority_calculation(self):
        graph = Graph("TEST")
        f1 = graph.register("GOAL-DEF.1")
        f2 = graph.register("GOAL-INST.1", isa="TEST.GOAL-DEF.1")
        f3 = graph.register("PRIORITY-CALC.1")

        f1["PRIORITY-CALCULATION"] = f3

        goal = Goal(f2)
        goal.inherit()
        self.assertEqual(f3, goal.frame["PRIORITY-CALCULATION"][0].resolve())

    def test_inherits_non_instanced_action_selection(self):
        graph = Graph("TEST")
        f1 = graph.register("GOAL-DEF.1")
        f2 = graph.register("ACTION-SELECTION.1", isa="TEST.GOAL-DEF.1")
        f3 = graph.register("ACTION-CALC.1")

        f1["ACTION-SELECTION"] = f3

        goal = Goal(f2)
        goal.inherit()
        self.assertEqual(f3, goal.frame["ACTION-SELECTION"][0].resolve())

    # TODO: how to inherit GOAL-STATE and HAS-GOAL?


class ConditionTestCase(unittest.TestCase):

    def test_order(self):
        graph = Graph("TEST")
        gc = graph.register("GOAL-CONDITION.1")
        gc["ORDER"] = 1

        self.assertEqual(Condition(gc).order(), 1)

    def test_status(self):
        graph = Graph("TEST")
        gc = graph.register("GOAL-CONDITION.1")
        gc["APPLY-STATUS"] = Literal(Goal.Status.SATISFIED.name)

        self.assertEqual(Condition(gc).status(), Goal.Status.SATISFIED)

    def test_assess_with(self):
        graph = Graph("TEST")
        gc = graph.register("GOAL-CONDITION.1")
        wc = graph.register("COLOR.1")
        obj = graph.register("OBJECT.1")

        gc["WITH-CONDITION"] = wc
        wc["DOMAIN"] = obj
        wc["RANGE"] = "yellow"

        condition = Condition(gc)

        self.assertFalse(condition._assess_with(wc))

        obj["COLOR"] = "yellow"

        self.assertTrue(condition._assess_with(wc))

    def test_assess_and(self):
        graph = Graph("TEST")
        gc = graph.register("GOAL-CONDITION.1")
        wc1 = graph.register("COLOR.1")
        wc2 = graph.register("NAME.1")
        obj = graph.register("OBJECT.1")

        gc["WITH-CONDITION"] = [wc1, wc2]
        gc["LOGIC"] = Literal(Condition.Logic.AND.name)
        wc1["DOMAIN"] = obj
        wc1["RANGE"] = "yellow"
        wc2["DOMAIN"] = obj
        wc2["RANGE"] = "Test"

        condition = Condition(gc)

        self.assertFalse(condition.assess())

        obj["COLOR"] = "yellow"

        self.assertFalse(condition.assess())

        obj["NAME"] = "Test"

        self.assertTrue(condition.assess())

    def test_assess_or(self):
        graph = Graph("TEST")
        gc = graph.register("GOAL-CONDITION.1")
        wc1 = graph.register("COLOR.1")
        wc2 = graph.register("NAME.1")
        obj = graph.register("OBJECT.1")

        gc["WITH-CONDITION"] = [wc1, wc2]
        gc["LOGIC"] = Literal(Condition.Logic.OR.name)
        wc1["DOMAIN"] = obj
        wc1["RANGE"] = "yellow"
        wc2["DOMAIN"] = obj
        wc2["RANGE"] = "Test"

        condition = Condition(gc)

        self.assertFalse(condition.assess())

        obj["COLOR"] = "yellow"

        self.assertTrue(condition.assess())

    def test_assess_not(self):
        graph = Graph("TEST")
        gc = graph.register("GOAL-CONDITION.1")
        wc1 = graph.register("COLOR.1")
        wc2 = graph.register("NAME.1")
        obj = graph.register("OBJECT.1")

        gc["WITH-CONDITION"] = [wc1, wc2]
        gc["LOGIC"] = Literal(Condition.Logic.NOT.name)
        wc1["DOMAIN"] = obj
        wc1["RANGE"] = "yellow"
        wc2["DOMAIN"] = obj
        wc2["RANGE"] = "Test"

        condition = Condition(gc)

        self.assertTrue(condition.assess())

        obj["COLOR"] = "yellow"

        self.assertFalse(condition.assess())

        obj["Name"] = "Test"

        self.assertFalse(condition.assess())

    def test_assess_no_conditions(self):
        graph = Graph("TEST")
        gc = graph.register("GOAL-CONDITION.1")
        self.assertTrue(Condition(gc).assess())


class ActionTestCase(unittest.TestCase):

    def test_execute(self):

        executed = False

        def execute_action(agent):
            nonlocal executed
            executed = True

        MPRegistry[execute_action.__name__] = execute_action

        graph = Graph("TEST")
        f1 = graph.register("ACTION.1")
        f2 = graph.register("MEANING-PROCEDURE.1")

        f1["RUN"] = f2
        f2["CALLS"] = Literal(execute_action.__name__)

        action = Action(f1)

        action.execute(None)
        self.assertTrue(executed)