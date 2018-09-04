from backend.models.agenda import Action, Agenda, Condition, Goal
from backend.models.graph import Frame, Graph, Literal
from backend.models.statement import Statement, VariableMap

import unittest


class AgendaTestCase(unittest.TestCase):

    def test_goals(self):
        graph = Graph("TEST")
        f1 = graph.register("AGENDA.1")  # Typically the agent identity frame (so, e.g., ROBOT.1) is used, as there is no "AGENDA".
        g1 = graph.register("GOAL.1")
        g2 = graph.register("GOAL.2")
        g3 = graph.register("GOAL.3")
        g4 = graph.register("GOAL.4")

        f1["HAS-GOAL"] = [g1, g2, g3, g4]

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

    def test_plan(self):
        graph = Graph("TEST")
        goal = graph.register("GOAL.1")
        action1 = graph.register("ACTION.1")
        action2 = graph.register("ACTION.2")

        goal["PLAN"] = [action1, action2]
        action2["SELECT"] = Literal(Action.DEFAULT)

        self.assertEqual(Goal(goal).plan(), action2)
        self.assertIsInstance(Goal(goal).plan(), Action)

    def test_assess(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return True

        graph = Statement.hierarchy()
        goal = graph.register("GOAL.1")
        condition1 = graph.register("CONDITION.1")
        condition2 = graph.register("CONDITION.2")
        statement = graph.register("STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")

        graph["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        goal["WHEN"] = [condition1, condition2]
        condition1["ORDER"] = 2
        condition2["ORDER"] = 1
        condition1["STATUS"] = Goal.Status.ABANDONED
        condition2["STATUS"] = Goal.Status.SATISFIED
        condition1["IF"] = statement
        condition2["IF"] = statement

        Goal(goal).assess()
        self.assertTrue(Goal(goal).is_satisfied())

    def test_instance_of(self):
        graph = Graph("TEST")
        definition = graph.register("GOAL-DEF")
        action = graph.register("ACTION.1")
        condition = graph.register("CONDITION.1")

        definition["NAME"] = Literal("Test Goal")
        definition["PRIORITY"] = 0.5
        definition["PLAN"] = action
        definition["WHEN"] = condition
        definition["WITH"] = Literal("VAR_X")

        params = [123]
        goal = Goal.instance_of(graph, definition, params)

        self.assertEqual(goal.name(), "Test Goal")
        self.assertTrue(goal.frame["PRIORITY"] == 0.5)
        self.assertTrue(goal.frame["PLAN"] == action)
        self.assertTrue(goal.frame["WHEN"] == condition)
        self.assertTrue(goal.frame["WITH"] == "VAR_X")
        self.assertEqual(1, len(goal.frame["_WITH"]))

        var = goal.frame["_WITH"][0].resolve()
        self.assertEqual(var["NAME"], "VAR_X")
        self.assertEqual(var["FROM"], goal.frame)
        self.assertEqual(var["VALUE"], 123)


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


class ActionTestCase(unittest.TestCase):

    def test_name(self):
        graph = Graph("TEST")
        action = graph.register("ACTION.1")
        action["NAME"] = Literal("Test Action")

        self.assertEqual(Action(action).name(), "Test Action")

    def test_select(self):

        result = True

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return result

        graph = Statement.hierarchy()
        action = graph.register("ACTION.1")
        statement = graph.register("BOOLEAN-STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")

        action["SELECT"] = statement
        graph["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        self.assertTrue(Action(action).select(None))

        result = False

        self.assertFalse(Action(action).select(None))

    def test_select_with_variable(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return varmap.resolve("X")

        graph = Statement.hierarchy()
        varmap = graph.register("VARMAP.1")
        variable = graph.register("VARIABLE.1")
        action = graph.register("ACTION.1")
        statement = graph.register("BOOLEAN-STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")

        varmap["_WITH"] = variable
        variable["NAME"] = Literal("X")
        variable["VALUE"] = True
        action["SELECT"] = statement
        graph["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        self.assertTrue(Action(action).select(VariableMap(varmap)))

    def test_select_when_default(self):
        graph = Statement.hierarchy()
        action = graph.register("ACTION.1")
        action["SELECT"] = Literal(Action.DEFAULT)

        self.assertTrue(Action(action).select(None))

    def test_is_default(self):
        graph = Statement.hierarchy()
        action = graph.register("ACTION.1")

        self.assertFalse(Action(action).is_default())

        action["SELECT"] = Literal(Action.DEFAULT)

        self.assertTrue(Action(action).is_default())

    def test_perform(self):

        out = []

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                nonlocal out
                out.append(self.frame["LOCAL"][0].resolve().value)

        graph = Statement.hierarchy()
        action = graph.register("ACTION.1")
        statement1 = graph.register("STATEMENT.1", isa="EXE.STATEMENT")
        statement2 = graph.register("STATEMENT.2", isa="EXE.STATEMENT")

        graph["STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        action["PERFORM"] = [statement1, statement2]
        statement1["LOCAL"] = Literal("X")
        statement2["LOCAL"] = Literal("Y")

        Action(action).perform(None)

        self.assertEqual(out, ["X", "Y"])

    def test_perform_with_variables(self):
        out = []

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                nonlocal out
                out.append(varmap.resolve("X"))

        graph = Statement.hierarchy()
        action = graph.register("ACTION.1")
        statement = graph.register("STATEMENT.1", isa="EXE.STATEMENT")
        varmap = graph.register("VARMAP.1")
        variable = graph.register("VARIABLE.1")

        graph["STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        action["PERFORM"] = statement
        varmap["_WITH"] = variable
        variable["NAME"] = Literal("X")
        variable["VALUE"] = 123

        Action(action).perform(VariableMap(varmap))

        self.assertEqual(out, [123])

    def test_perform_idle(self):
        graph = Statement.hierarchy()
        action = graph.register("ACTION.1")
        action["PERFORM"] = Literal(Action.IDLE)

        Action(action).perform(None)