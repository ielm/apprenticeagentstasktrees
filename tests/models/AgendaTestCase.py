from backend.models.agenda import Action, Agenda, Condition, Goal, Variable
from backend.models.graph import Frame, Graph, Literal
from backend.models.mps import MPRegistry
from backend.models.statement import Statement, VariableMap

import unittest


# class AgendaTestCase(unittest.TestCase):
#
#     def test_goals(self):
#         graph = Graph("TEST")
#         f1 = graph.register("AGENDA.1")  # Typically the agent identity frame (so, e.g., ROBOT.1) is used, as there is no "AGENDA".
#         g1 = graph.register("GOAL.1")
#         g2 = graph.register("GOAL.2")
#         g3 = graph.register("GOAL.3")
#         g4 = graph.register("GOAL.4")
#
#         f1["GOAL"] = [g1, g2, g3, g4]
#
#         g1["STATUS"] = "pending"
#         g2["STATUS"] = "active"
#         g3["STATUS"] = "abandoned"
#         g4["STATUS"] = "satisfied"
#
#         agenda = Agenda(f1)
#         self.assertEqual(agenda.goals(), [Goal(g2)])
#         self.assertEqual(agenda.goals(pending=True), [Goal(g1), Goal(g2)])
#         self.assertEqual(agenda.goals(active=False), [])
#         self.assertEqual(agenda.goals(abandoned=True, active=False), [Goal(g3)])
#         self.assertEqual(agenda.goals(satisfied=True, active=False), [Goal(g4)])
#
#     def test_add_goal(self):
#         graph = Graph("TEST")
#         f1 = graph.register("AGENDA.1")
#         g1 = graph.register("GOAL.1")
#         g2 = graph.register("GOAL.2")
#
#         agenda = Agenda(f1)
#         agenda.add_goal(g1)
#         agenda.add_goal(Goal(g2))
#
#         self.assertEqual(agenda.goals(pending=True), [Goal(g1), Goal(g2)])
#
#     def test_prepare_action(self):
#         graph = Graph("TEST")
#         f1 = graph.register("AGENDA.1")
#         a1 = graph.register("ACTION.1")
#         a2 = graph.register("ACTION.2")
#
#         agenda = Agenda(f1)
#
#         agenda.prepare_action(a1)
#         self.assertEqual(len(f1["ACTION-TO-TAKE"]), 1)
#         self.assertEqual(f1["ACTION-TO-TAKE"][0].resolve(), a1)
#
#         agenda.prepare_action(Action(a2))
#         self.assertEqual(len(f1["ACTION-TO-TAKE"]), 1)
#         self.assertEqual(f1["ACTION-TO-TAKE"][0].resolve(), a2)
#
#     def test_action(self):
#         graph = Graph("TEST")
#         f1 = graph.register("AGENDA.1")
#         a1 = graph.register("ACTION.1")
#
#         f1["ACTION-TO-TAKE"] = a1
#
#         agenda = Agenda(f1)
#         self.assertEqual(a1, agenda.action())
#         self.assertEqual(Action, agenda.action().__class__)


class GoalTestCase(unittest.TestCase):

    def test_name(self):
        f = Frame("TEST.1")
        f["NAME"] = Literal("Test Name")

        goal = Goal(f)
        self.assertEqual(goal.name(), "Test Name")

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

    def test_prioritize_numeric(self):

        graph = Graph("TEST")
        f = graph.register("GOAL.1")
        f["PRIORITY"] = 0.5

        goal = Goal(f)
        goal.prioritize(None)
        self.assertTrue(f["_PRIORITY"] == 0.5)

    @unittest.skip("Skipping test prioritize with calculation until CALCULATE-STATEMENT is defined.")
    def test_prioritize_calculation(self):

        fail() # TODO: CALCULATE-STATEMENT

    def test_priority(self):
        graph = Graph("TEST")
        f1 = graph.register("GOAL.1")

        goal = Goal(f1)
        self.assertEqual(0.0, goal.priority())

        f1["_PRIORITY"] = 0.5
        self.assertEqual(0.5, goal.priority())

    # def test_conditions(self):
    #     graph = Graph("TEST")
    #     g = graph.register("GOAL.1")
    #     gc = graph.register("GOAL-CONDITION.1")
    #
    #     g["ON-CONDITION"] = gc
    #
    #     goal = Goal(g)
    #     self.assertEqual(goal.conditions(), [Condition(gc)])
    #     self.assertEqual(goal.conditions()[0].frame, gc)
    #     self.assertIsInstance(goal.conditions()[0].frame, Frame)
    #
    # def test_assess(self):
    #     graph = Graph("TEST")
    #     g = graph.register("GOAL.1")
    #     gc = graph.register("GOAL-CONDITION.1")
    #     wc = graph.register("COLOR.1")
    #     obj = graph.register("OBJECT.1")
    #
    #     g["ON-CONDITION"] = gc
    #     g["STATUS"] = Literal(Goal.Status.ACTIVE.name)
    #     gc["WITH-CONDITION"] = wc
    #     gc["APPLY-STATUS"] = Literal(Goal.Status.SATISFIED.name)
    #     wc["DOMAIN"] = obj
    #     wc["RANGE"] = "yellow"
    #
    #     goal = Goal(g)
    #     self.assertTrue(goal.is_active())
    #
    #     goal.assess()
    #     self.assertTrue(goal.is_active())
    #
    #     obj["COLOR"] = "yellow"
    #     goal.assess()
    #     self.assertTrue(goal.is_satisfied())
    #
    # def test_assess_multiple_conditions(self):
    #     graph = Graph("TEST")
    #     g = graph.register("GOAL.1")
    #     gc1 = graph.register("GOAL-CONDITION.1")
    #     gc2 = graph.register("GOAL-CONDITION.2")
    #     wc = graph.register("COLOR.1")
    #     obj = graph.register("OBJECT.1")
    #
    #     g["ON-CONDITION"] = [gc1, gc2]
    #     g["STATUS"] = Literal(Goal.Status.ACTIVE.name)
    #     gc1["WITH-CONDITION"] = wc
    #     gc1["APPLY-STATUS"] = Literal(Goal.Status.SATISFIED.name)
    #     gc1["ORDER"] = 2
    #     gc2["WITH-CONDITION"] = wc
    #     gc2["APPLY-STATUS"] = Literal(Goal.Status.ABANDONED.name)
    #     gc2["ORDER"] = 1
    #     wc["DOMAIN"] = obj
    #     wc["RANGE"] = "yellow"
    #     obj["COLOR"] = "yellow"
    #
    #     goal = Goal(g)
    #     goal.assess()
    #     self.assertTrue(goal.is_abandoned())
    #
    # def test_subgoals(self):
    #     graph = Graph("TEST")
    #     f1 = graph.register("GOAL.1")
    #     f2 = graph.register("GOAL.2")
    #     f3 = graph.register("GOAL.3")
    #
    #     f1["HAS-GOAL"] = [f2, f3]
    #
    #     goal = Goal(f1)
    #     subgoals = goal.subgoals()
    #     subgoals = list(map(lambda subgoal: subgoal.frame, subgoals))
    #     self.assertTrue(f2 in subgoals)
    #     self.assertTrue(f3 in subgoals)
    #     self.assertIsInstance(subgoals[0], Frame)
    #
    # def test_pursue(self):
    #     def select_action(agent):
    #         return Frame("IDLE.1")  # Properties can be added here
    #
    #     MPRegistry.register(select_action)
    #
    #     graph = Graph("TEST")
    #     f1 = graph.register("GOAL.1")
    #     f2 = graph.register("MEANING-PROCEDURE.1")
    #
    #     f1["ACTION-SELECTION"] = f2
    #     f2["CALLS"] = Literal(select_action.__name__)
    #
    #     goal = Goal(f1)
    #
    #     action = goal.pursue(None)
    #     self.assertEqual("IDLE.1", action.frame.name())
    #
    # def test_inherits_non_instanced_priority_calculation(self):
    #     graph = Graph("TEST")
    #     f1 = graph.register("GOAL-DEF.1")
    #     f2 = graph.register("GOAL-INST.1", isa="TEST.GOAL-DEF.1")
    #     f3 = graph.register("PRIORITY-CALC.1")
    #
    #     f1["PRIORITY-CALCULATION"] = f3
    #
    #     goal = Goal(f2)
    #     goal.inherit()
    #     self.assertEqual(f3, goal.frame["PRIORITY-CALCULATION"][0].resolve())
    #
    # def test_inherits_non_instanced_action_selection(self):
    #     graph = Graph("TEST")
    #     f1 = graph.register("GOAL-DEF.1")
    #     f2 = graph.register("ACTION-SELECTION.1", isa="TEST.GOAL-DEF.1")
    #     f3 = graph.register("ACTION-CALC.1")
    #
    #     f1["ACTION-SELECTION"] = f3
    #
    #     goal = Goal(f2)
    #     goal.inherit()
    #     self.assertEqual(f3, goal.frame["ACTION-SELECTION"][0].resolve())
    #
    # def test_inherits_non_instanced_conditions(self):
    #     graph = Graph("TEST")
    #     f1 = graph.register("GOAL-DEF.1")
    #     f2 = graph.register("GOAL-INST.1", isa="TEST.GOAL-DEF.1")
    #     f3 = graph.register("GOAL-CONDITION.1")
    #
    #     f1["ON-CONDITION"] = f3
    #
    #     goal = Goal(f2)
    #     goal.inherit()
    #     self.assertEqual(f3, goal.frame["ON-CONDITION"][0].resolve())


class ConditionTestCase(unittest.TestCase):

    def test_order(self):
        graph = Graph("TEST")
        gc = graph.register("CONDITION.1")
        gc["ORDER"] = 1

        self.assertEqual(Condition(gc).order(), 1)

    def test_status(self):
        graph = Graph("TEST")
        gc = graph.register("GOAL-CONDITION.1")
        gc["STATUS"] = Literal(Goal.Status.SATISFIED.name)

        self.assertEqual(Condition(gc).status(), Goal.Status.SATISFIED)

    def test_requires_boolean_statement(self):
        graph = Statement.hierarchy()
        c = graph.register("CONDITION.1")
        b = graph.register("STATEMENT.1", isa="EXE.STATEMENT")

        c["IF"] = b

        with self.assertRaises(Exception):
            Condition(c)

    def test_assess_if(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return True

        graph = Statement.hierarchy()
        c = graph.register("CONDITION.1")
        b = graph.register("BOOLEAN-STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")
        graph["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        c["IF"] = b

        self.assertTrue(Condition(c)._assess_if(b, None))

    def test_assess_and(self):

        result1 = True
        result2 = True

        class TestStatement1(Statement):
            def run(self, varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, varmap: VariableMap):
                return result2

        graph = Statement.hierarchy()
        c = graph.register("CONDITION.1")
        graph.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        graph.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = graph.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = graph.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        graph["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        graph["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

        c["IF"] = [b1, b2]
        c["LOGIC"] = Condition.Logic.AND

        self.assertTrue(Condition(c).assess(None))

        result1 = True
        result2 = False

        self.assertFalse(Condition(c).assess(None))

    def test_assess_or(self):
        result1 = True
        result2 = True

        class TestStatement1(Statement):
            def run(self, varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, varmap: VariableMap):
                return result2

        graph = Statement.hierarchy()
        c = graph.register("CONDITION.1")
        graph.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        graph.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = graph.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = graph.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        graph["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        graph["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

        c["IF"] = [b1, b2]
        c["LOGIC"] = Condition.Logic.OR

        self.assertTrue(Condition(c).assess(None))

        result1 = True
        result2 = False

        self.assertTrue(Condition(c).assess(None))

    def test_assess_nor(self):
        result1 = True
        result2 = True

        class TestStatement1(Statement):
            def run(self, varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, varmap: VariableMap):
                return result2

        graph = Statement.hierarchy()
        c = graph.register("CONDITION.1")
        graph.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        graph.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = graph.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = graph.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        graph["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        graph["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

        c["IF"] = [b1, b2]
        c["LOGIC"] = Condition.Logic.NOR

        self.assertFalse(Condition(c).assess(None))

        result1 = True
        result2 = False

        self.assertFalse(Condition(c).assess(None))

        result1 = False
        result2 = False

        self.assertTrue(Condition(c).assess(None))

    def test_assess_nand(self):
        result1 = True
        result2 = True

        class TestStatement1(Statement):
            def run(self, varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, varmap: VariableMap):
                return result2

        graph = Statement.hierarchy()
        c = graph.register("CONDITION.1")
        graph.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        graph.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = graph.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = graph.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        graph["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        graph["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

        c["IF"] = [b1, b2]
        c["LOGIC"] = Condition.Logic.NAND

        self.assertFalse(Condition(c).assess(None))

        result1 = True
        result2 = False

        self.assertTrue(Condition(c).assess(None))

        result1 = False
        result2 = False

        self.assertTrue(Condition(c).assess(None))

    def test_assess_not(self):
        result1 = True
        result2 = True

        class TestStatement1(Statement):
            def run(self, varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, varmap: VariableMap):
                return result2

        graph = Statement.hierarchy()
        c = graph.register("CONDITION.1")
        graph.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        graph.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = graph.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = graph.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        graph["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        graph["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

        c["IF"] = [b1, b2]
        c["LOGIC"] = Condition.Logic.NOT

        self.assertFalse(Condition(c).assess(None))

        result1 = True
        result2 = False

        self.assertFalse(Condition(c).assess(None))

        result1 = False
        result2 = False

        self.assertTrue(Condition(c).assess(None))

    def test_assess_no_conditions(self):
        graph = Graph("TEST")
        gc = graph.register("GOAL-CONDITION.1")
        self.assertTrue(Condition(gc).assess(None))

    def test_assess_with_varmap(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return varmap.resolve("X")

        graph = Statement.hierarchy()
        c = graph.register("CONDITION.1")
        b = graph.register("BOOLEAN-STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")
        graph["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        vm = graph.register("VARMAP.1")
        v = graph.register("VARIABLE.1")

        vm["WITH"] = Literal("X")
        vm["_WITH"] = v
        v["NAME"] = Literal("X")
        v["VALUE"] = True

        c["IF"] = b

        self.assertTrue(Condition(c).assess(VariableMap(vm)))


# class ActionTestCase(unittest.TestCase):
#
#     def test_execute(self):
#
#         executed = False
#
#         def execute_action(agent):
#             nonlocal executed
#             executed = True
#
#         MPRegistry.register(execute_action)
#
#         graph = Graph("TEST")
#         f1 = graph.register("ACTION.1")
#         f2 = graph.register("MEANING-PROCEDURE.1")
#
#         f1["RUN"] = f2
#         f2["CALLS"] = Literal(execute_action.__name__)
#
#         action = Action(f1)
#
#         action.execute(None)
#         self.assertTrue(executed)