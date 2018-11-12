from backend.models.agenda import Action, Agenda, Condition, Goal, Trigger
from backend.models.graph import Frame, Graph, Literal, Network
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
        self.assertEqual(len(f1["ACTION-TO-TAKE"]), 2)
        self.assertEqual(f1["ACTION-TO-TAKE"][0].resolve(), a1)
        self.assertEqual(f1["ACTION-TO-TAKE"][1].resolve(), a2)

    def test_action(self):
        graph = Graph("TEST")
        f1 = graph.register("AGENDA.1")
        a1 = graph.register("ACTION.1")

        f1["ACTION-TO-TAKE"] = a1

        agenda = Agenda(f1)
        self.assertEqual([a1], agenda.action())

    def test_triggers(self):
        n = Network()
        graph = n.register(Graph("TEST"))
        agenda = graph.register("AGENDA")
        definition = graph.register("MYGOAL")

        query1 = Frame.q(n).isa("TEST1")
        query2 = Frame.q(n).isa("TEST2")

        trigger1 = Trigger.build(graph, query1, definition)
        trigger2 = Trigger.build(graph, query2, definition)

        agenda["TRIGGER"] += trigger1.frame
        agenda["TRIGGER"] += trigger2.frame

        self.assertEqual([trigger1, trigger2], Agenda(agenda).triggers())

    def test_add_trigger(self):
        n = Network()
        graph = n.register(Graph("TEST"))
        agenda = graph.register("AGENDA")
        definition = graph.register("MYGOAL")

        query = Frame.q(n).isa("TEST1")

        trigger = Trigger.build(graph, query, definition)

        Agenda(agenda).add_trigger(trigger)

        self.assertEqual([trigger], Agenda(agenda).triggers())

    def test_fire_triggers(self):
        n = Network()
        graph = n.register(Graph("TEST"))
        agenda = Agenda(graph.register("AGENDA"))

        definition = graph.register("MYGOAL")
        definition["WITH"] = Literal("$var1")

        trigger1 = Trigger.build(graph, Frame.q(n).id("TEST.TARGET.1"), definition)
        agenda.add_trigger(trigger1)

        trigger2 = Trigger.build(graph, Frame.q(n).id("TEST.TARGET.1"), definition)
        agenda.add_trigger(trigger2)

        target = graph.register("TARGET", generate_index=True)

        self.assertEqual(0, len(agenda.goals(pending=True, active=True)))

        agenda.fire_triggers()

        self.assertIn(graph["GOAL.1"], agenda.goals(pending=True, active=True))
        self.assertEqual(target, Goal(graph["GOAL.1"]).resolve("$var1"))

        self.assertIn(graph["GOAL.2"], agenda.goals(pending=True, active=True))
        self.assertEqual(target, Goal(graph["GOAL.2"]).resolve("$var1"))


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
        self.assertTrue(Goal.Status.PENDING in f["STATUS"])
        self.assertFalse(Goal.Status.ACTIVE in f["STATUS"])
        self.assertFalse(Goal.Status.ABANDONED in f["STATUS"])
        self.assertFalse(Goal.Status.SATISFIED in f["STATUS"])

        goal.status(Goal.Status.ACTIVE)
        self.assertFalse(Goal.Status.PENDING in f["STATUS"])
        self.assertTrue(Goal.Status.ACTIVE in f["STATUS"])
        self.assertFalse(Goal.Status.ABANDONED in f["STATUS"])
        self.assertFalse(Goal.Status.SATISFIED in f["STATUS"])

        goal.status(Goal.Status.ABANDONED)
        self.assertFalse(Goal.Status.PENDING in f["STATUS"])
        self.assertFalse(Goal.Status.ACTIVE in f["STATUS"])
        self.assertTrue(Goal.Status.ABANDONED in f["STATUS"])
        self.assertFalse(Goal.Status.SATISFIED in f["STATUS"])

        goal.status(Goal.Status.SATISFIED)
        self.assertFalse(Goal.Status.PENDING in f["STATUS"])
        self.assertFalse(Goal.Status.ACTIVE in f["STATUS"])
        self.assertFalse(Goal.Status.ABANDONED in f["STATUS"])
        self.assertTrue(Goal.Status.SATISFIED in f["STATUS"])

    def test_priority_numeric(self):

        graph = Graph("TEST")
        f = graph.register("GOAL.1")
        f["PRIORITY"] = 0.5

        goal = Goal(f)
        self.assertEqual(goal.priority(None), 0.5)
        self.assertTrue(f["_PRIORITY"] == 0.5)

    def test_priority_calculation(self):
        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return 0.5

        graph = Statement.hierarchy()
        graph["RETURNING-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        statement = graph.register("STATEMENT.1", isa="EXE.RETURNING-STATEMENT")

        f = graph.register("GOAL.1")
        f["PRIORITY"] = statement

        goal = Goal(f)
        self.assertEqual(goal.priority(None), 0.5)
        self.assertTrue(f["_PRIORITY"] == 0.5)

    def test_priority(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")

        goal = Goal(f)
        self.assertEqual(0.0, goal.priority(None))
        self.assertTrue(f["_PRIORITY"] == 0.0)

    def test_cached_priority(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")

        goal = Goal(f)
        self.assertEqual(0.0, goal._cached_priority())
        self.assertEqual(0.0, goal.priority(None))
        self.assertEqual(0.0, goal._cached_priority())

    def test_resources_numeric(self):

        graph = Graph("TEST")
        f = graph.register("GOAL.1")
        f["RESOURCES"] = 0.5

        goal = Goal(f)
        self.assertEqual(goal.resources(None), 0.5)
        self.assertTrue(f["_RESOURCES"] == 0.5)

    def test_resources_calculation(self):
        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return 0.5

        graph = Statement.hierarchy()
        graph["RETURNING-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        statement = graph.register("STATEMENT.1", isa="EXE.RETURNING-STATEMENT")

        f = graph.register("GOAL.1")
        f["RESOURCES"] = statement

        goal = Goal(f)
        self.assertEqual(goal.resources(None), 0.5)
        self.assertTrue(f["_RESOURCES"] == 0.5)

    def test_resources(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")

        goal = Goal(f)
        self.assertEqual(1.0, goal.resources(None))
        self.assertTrue(f["_RESOURCES"] == 1.0)

    def test_cached_resources(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")

        goal = Goal(f)
        self.assertEqual(1.0, goal._cached_resources())
        self.assertEqual(1.0, goal.resources(None))
        self.assertEqual(1.0, goal._cached_resources())

    def test_assign_decision(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")
        goal = Goal(f)
        goal.decision(decide=0.5)
        self.assertTrue(0.5 in f["_DECISION"])

    def test_cached_decision(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")

        goal = Goal(f)
        self.assertEqual(0.0, goal.decision())

        f["_DECISION"] = 0.5
        self.assertEqual(0.5, goal.decision())

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

    def test_assess_ignores_conditions_if_goal_is_using_effector(self):
        from backend.models.effectors import Capability, Effector
        from backend.models.statement import IsStatement

        graph = Statement.hierarchy()
        graph.register("EFFECTOR")
        graph.register("MENTAL-EFFECTOR", isa="EXE.EFFECTOR")
        target = graph.register("TARGET")
        target["X"] = 1

        # 1) Define a goal and make an instance of it; the goal's state is active, and it's condition will be satisfied
        statement = IsStatement.instance(graph, target, "X", 1)
        condition = Condition.build(graph, [statement], Goal.Status.SATISFIED)
        definition = Goal.define(graph, "TEST", 0.5, 0.5, [], [condition], [])
        goal = Goal.instance_of(graph, definition, [])
        goal.status(Goal.Status.ACTIVE)

        # 2) Create an effector and capability, and reserve them for the goal
        capability = Capability.instance(graph, "CAP", "")
        effector = Effector.instance(graph, Effector.Type.MENTAL, [capability])
        effector.reserve(goal, capability)

        # 3) The goal is active, the condition is satisified, but assessing the goal remains active (due to the effector)
        self.assertTrue(goal.is_active())
        self.assertTrue(condition.assess(None))
        goal.assess()
        self.assertTrue(goal.is_active())

        # 4) Release the effector, and now the goal will assess using the condition
        effector.release()
        goal.assess()
        self.assertTrue(goal.is_satisfied())

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


class TriggerTestCase(unittest.TestCase):

    def test_query(self):
        n = Network()

        query = Frame.q(n).id("TEST.FRAME.123")

        graph = n.register(Graph("TEST"))
        trigger = graph.register("TRIGGER")
        trigger["QUERY"] = query

        self.assertEqual(query, Trigger(trigger).query())

    def test_definition(self):
        n = Network()
        graph = n.register(Graph("TEST"))
        goal = graph.register("MYGOAL")
        trigger = graph.register("TRIGGER")
        trigger["DEFINITION"] = goal

        self.assertEqual(goal, Trigger(trigger).definition())

    def test_fire_creates_goal_instance(self):
        n = Network()
        graph = n.register(Graph("TEST"))
        agenda = Agenda(graph.register("AGENDA"))

        definition = graph.register("MYGOAL")
        definition["WITH"] = Literal("$var1")

        trigger = Trigger.build(graph, Frame.q(n).id("TEST.TARGET.1"), definition)
        agenda.add_trigger(trigger)

        target = graph.register("TARGET", generate_index=True)

        self.assertEqual(0, len(agenda.goals(pending=True, active=True)))

        trigger.fire(agenda)

        self.assertIn(graph["GOAL.1"], agenda.goals(pending=True, active=True))
        self.assertEqual(target, Goal(graph["GOAL.1"]).resolve("$var1"))

    def test_fire_creates_multiple_goal_instances(self):
        n = Network()
        graph = n.register(Graph("TEST"))
        agenda = Agenda(graph.register("AGENDA"))

        definition = graph.register("MYGOAL")
        definition["WITH"] = Literal("$var1")

        trigger = Trigger.build(graph, Frame.q(n).has("MYSLOT"), definition)

        target1 = graph.register("TARGET", generate_index=True)
        target1["MYSLOT"] = 123

        target2 = graph.register("TARGET", generate_index=True)
        target2["MYSLOT"] = 123

        self.assertEqual(0, len(agenda.goals(pending=True, active=True)))

        trigger.fire(agenda)

        self.assertIn(graph["GOAL.1"], agenda.goals(pending=True, active=True))
        self.assertIn(graph["GOAL.2"], agenda.goals(pending=True, active=True))
        self.assertEqual(target1, Goal(graph["GOAL.1"]).resolve("$var1"))
        self.assertEqual(target2, Goal(graph["GOAL.2"]).resolve("$var1"))

    def test_fire_filters_existing_triggered_instances(self):
        n = Network()
        graph = n.register(Graph("TEST"))
        agenda = Agenda(graph.register("AGENDA"))

        definition = graph.register("MYGOAL")
        definition["WITH"] = Literal("$var1")

        trigger = Trigger.build(graph, Frame.q(n).has("MYSLOT"), definition)

        target1 = graph.register("TARGET", generate_index=True)
        target1["MYSLOT"] = 123

        self.assertEqual(0, len(agenda.goals(pending=True, active=True)))

        trigger.fire(agenda)

        self.assertIn(graph["GOAL.1"], agenda.goals(pending=True, active=True))
        self.assertEqual(target1, Goal(graph["GOAL.1"]).resolve("$var1"))

        target2 = graph.register("TARGET", generate_index=True)
        target2["MYSLOT"] = 123

        trigger.fire(agenda)

        self.assertIn(graph["GOAL.2"], agenda.goals(pending=True, active=True))
        self.assertEqual(target2, Goal(graph["GOAL.2"]).resolve("$var1"))

        self.assertEqual(2, len(agenda.goals(pending=True, active=True)))


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

    def test_capabilities(self):
        from backend.models.effectors import Capability
        from backend.models.statement import CapabilityStatement, ForEachStatement

        graph = Statement.hierarchy()

        cap1 = Capability.instance(graph, "CAPABILITY-A", "")
        cap2 = Capability.instance(graph, "CAPABILITY-B", "")

        stmt1 = CapabilityStatement.instance(graph, cap1, [], [])
        stmt2 = CapabilityStatement.instance(graph, cap2, [], [])
        stmt3 = ForEachStatement.instance(graph, None, "$var1", stmt2)

        action = Action.build(graph, "TEST", Action.DEFAULT, [stmt1, stmt3])

        self.assertEqual([cap1, cap2], action.capabilities(None))