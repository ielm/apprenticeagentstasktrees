from backend.models.agenda import Agenda, Condition, Decision, Expectation, Goal, Plan, Step, Trigger
from backend.models.bootstrap import Bootstrap
from backend.models.graph import Frame, Graph, Literal, Network
from backend.models.statement import Statement, StatementScope, VariableMap

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

    def test_prepare_plan(self):
        graph = Graph("TEST")
        f1 = graph.register("AGENDA.1")
        a1 = graph.register("PLAN.1")
        a2 = graph.register("PLAN.2")

        agenda = Agenda(f1)

        agenda.prepare_plan(a1)
        self.assertEqual(len(f1["PLAN-TO-TAKE"]), 1)
        self.assertEqual(f1["PLAN-TO-TAKE"][0].resolve(), a1)

        agenda.prepare_plan(Plan(a2))
        self.assertEqual(len(f1["PLAN-TO-TAKE"]), 2)
        self.assertEqual(f1["PLAN-TO-TAKE"][0].resolve(), a1)
        self.assertEqual(f1["PLAN-TO-TAKE"][1].resolve(), a2)

    def test_plan(self):
        graph = Graph("TEST")
        f1 = graph.register("AGENDA.1")
        a1 = graph.register("PLAN.1")

        f1["PLAN-TO-TAKE"] = a1

        agenda = Agenda(f1)
        self.assertEqual([a1], agenda.plan())

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

    def test_executed_is_true_if_any_plan_is_complete(self):
        g = Graph("TEST")

        step1 = Step.build(g, 1, [])
        step2 = Step.build(g, 1, [])

        plan1 = Plan.build(g, "test-plan-1", Plan.DEFAULT, [step1])
        plan2 = Plan.build(g, "test-plan-2", Plan.DEFAULT, [step2])

        goal = g.register("GOAL.1")
        goal["PLAN"] = [plan1.frame, plan2.frame]

        self.assertFalse(Goal(goal).executed())

        step1.frame["STATUS"] = Step.Status.FINISHED

        self.assertTrue(Goal(goal).executed())

    def test_priority_numeric(self):

        graph = Graph("TEST")
        f = graph.register("GOAL.1")
        f["PRIORITY"] = 0.5

        goal = Goal(f)
        self.assertEqual(goal.priority(), 0.5)
        self.assertTrue(f["_PRIORITY"] == 0.5)

    def test_priority_calculation(self):
        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return 0.5

        network = Network()
        graph = network.register("EXE")
        Bootstrap.bootstrap_resource(network, "backend.resources", "exe.knowledge")

        graph["RETURNING-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        statement = graph.register("STATEMENT.1", isa="EXE.RETURNING-STATEMENT")

        f = graph.register("GOAL.1")
        f["PRIORITY"] = statement

        goal = Goal(f)
        self.assertEqual(goal.priority(), 0.5)
        self.assertTrue(f["_PRIORITY"] == 0.5)

    def test_priority(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")

        goal = Goal(f)
        self.assertEqual(0.0, goal.priority())
        self.assertTrue(f["_PRIORITY"] == 0.0)

    def test_cached_priority(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")

        goal = Goal(f)
        self.assertEqual(0.0, goal._cached_priority())
        self.assertEqual(0.0, goal.priority())
        self.assertEqual(0.0, goal._cached_priority())

    def test_resources_numeric(self):

        graph = Graph("TEST")
        f = graph.register("GOAL.1")
        f["RESOURCES"] = 0.5

        goal = Goal(f)
        self.assertEqual(goal.resources(), 0.5)
        self.assertTrue(f["_RESOURCES"] == 0.5)

    def test_resources_calculation(self):
        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return 0.5

        network = Network()
        graph = network.register("EXE")
        Bootstrap.bootstrap_resource(network, "backend.resources", "exe.knowledge")

        graph["RETURNING-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        statement = graph.register("STATEMENT.1", isa="EXE.RETURNING-STATEMENT")

        f = graph.register("GOAL.1")
        f["RESOURCES"] = statement

        goal = Goal(f)
        self.assertEqual(goal.resources(), 0.5)
        self.assertTrue(f["_RESOURCES"] == 0.5)

    def test_resources(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")

        goal = Goal(f)
        self.assertEqual(1.0, goal.resources())
        self.assertTrue(f["_RESOURCES"] == 1.0)

    def test_cached_resources(self):
        graph = Graph("TEST")
        f = graph.register("GOAL.1")

        goal = Goal(f)
        self.assertEqual(1.0, goal._cached_resources())
        self.assertEqual(1.0, goal.resources())
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
        plan1 = graph.register("PLAN.1")
        plan2 = graph.register("PLAN.2")

        goal["PLAN"] = [plan1, plan2]
        plan2["SELECT"] = Literal(Plan.DEFAULT)

        self.assertEqual(Goal(goal).plan(), plan2)
        self.assertIsInstance(Goal(goal).plan(), Plan)

    def test_assess(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return True

        network = Network()
        graph = network.register("EXE")
        Bootstrap.bootstrap_resource(network, "backend.resources", "exe.knowledge")

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

    def test_assess_abandons_subgoals_if_goal_satisfied(self):
        network = Network()
        graph = network.register("EXE")

        subgoal1 = graph.register("SUBGOAL.1")
        subgoal1["STATUS"] = Goal.Status.ACTIVE

        subgoal2 = graph.register("SUBGOAL.2")
        subgoal2["STATUS"] = Goal.Status.SATISFIED

        goal = graph.register("GOAL.1")
        goal["STATUS"] = Goal.Status.ACTIVE
        goal["HAS-GOAL"] += subgoal1
        goal["HAS-GOAL"] += subgoal2

        self.assertEqual([subgoal1, subgoal2], Goal(goal).subgoals())
        self.assertTrue(Goal(subgoal1).is_active())
        self.assertTrue(Goal(subgoal2).is_satisfied())

        goal["STATUS"] = Goal.Status.SATISFIED
        Goal(goal).assess()

        self.assertEqual([subgoal1, subgoal2], Goal(goal).subgoals())
        self.assertTrue(Goal(subgoal1).is_abandoned())
        self.assertTrue(Goal(subgoal2).is_satisfied())

    def test_assess_abandons_subgoals_if_goal_abandoned(self):
        network = Network()
        graph = network.register("EXE")

        subgoal1 = graph.register("SUBGOAL.1")
        subgoal1["STATUS"] = Goal.Status.ACTIVE

        subgoal2 = graph.register("SUBGOAL.2")
        subgoal2["STATUS"] = Goal.Status.SATISFIED

        goal = graph.register("GOAL.1")
        goal["STATUS"] = Goal.Status.ACTIVE
        goal["HAS-GOAL"] += subgoal1
        goal["HAS-GOAL"] += subgoal2

        self.assertEqual([subgoal1, subgoal2], Goal(goal).subgoals())
        self.assertTrue(Goal(subgoal1).is_active())
        self.assertTrue(Goal(subgoal2).is_satisfied())

        goal["STATUS"] = Goal.Status.ABANDONED
        Goal(goal).assess()

        self.assertEqual([subgoal1, subgoal2], Goal(goal).subgoals())
        self.assertTrue(Goal(subgoal1).is_abandoned())
        self.assertTrue(Goal(subgoal2).is_satisfied())

    def test_instance_of(self):
        graph = Graph("TEST")
        definition = graph.register("GOAL-DEF")
        plan = graph.register("PLAN.1")
        condition = graph.register("CONDITION.1")

        plan["SELECT"] = Literal(Plan.DEFAULT)

        definition["NAME"] = Literal("Test Goal")
        definition["PRIORITY"] = 0.5
        definition["PLAN"] = plan
        definition["WHEN"] = condition
        definition["WITH"] = Literal("VAR_X")

        params = [123]
        goal = Goal.instance_of(graph, definition, params)

        self.assertEqual(goal.name(), "Test Goal")
        self.assertTrue(goal.frame["PRIORITY"] == 0.5)
        self.assertTrue(goal.frame["PLAN"] == plan)
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

    def test_triggered_on(self):
        n = Network()
        graph = n.register(Graph("TEST"))
        o1 = graph.register("OBJECT.1")
        o2 = graph.register("OBJECT.2")

        trigger = graph.register("TRIGGER")

        trigger["TRIGGERED-ON"] += "TEST.OBJECT.1"
        trigger["TRIGGERED-ON"] += "TEST.OBJECT.2"

        self.assertEqual([o1, o2], Trigger(trigger).triggered_on())

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

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_order(self):
        gc = self.g.register("CONDITION.1")
        gc["ORDER"] = 1

        self.assertEqual(Condition(gc).order(), 1)

    def test_status(self):
        gc = self.g.register("GOAL-CONDITION.1")
        gc["STATUS"] = Literal(Goal.Status.SATISFIED.name)

        self.assertEqual(Condition(gc).status(), Goal.Status.SATISFIED)

    def test_on(self):
        gc = self.g.register("GOAL-CONDITION.1")
        gc["ON"] = Literal(Condition.On.EXECUTED)

        self.assertEqual(Condition(gc).on(), Condition.On.EXECUTED)

    def test_requires_boolean_statement(self):
        c = self.g.register("CONDITION.1")
        b = self.g.register("STATEMENT.1", isa="EXE.STATEMENT")

        c["IF"] = b

        with self.assertRaises(Exception):
            Condition(c)

    def test_assess_executed(self):
        goal = self.g.register("GOAL")

        condition = self.g.register("CONDITION")
        condition["ON"] = Condition.On.EXECUTED

        self.assertFalse(Condition(condition).assess(VariableMap(goal)))

        goal["PLAN"] = self.g.register("PLAN")

        self.assertTrue(Condition(condition).assess(VariableMap(goal)))

    def test_assess_if(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return True

        c = self.g.register("CONDITION.1")
        b = self.g.register("BOOLEAN-STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")
        self.g["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        c["IF"] = b

        self.assertTrue(Condition(c)._assess_if(b, None))

    def test_assess_and(self):

        result1 = True
        result2 = True

        class TestStatement1(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        c = self.g.register("CONDITION.1")
        self.g.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        self.g.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = self.g.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = self.g.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        self.g["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        self.g["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

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
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        c = self.g.register("CONDITION.1")
        self.g.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        self.g.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = self.g.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = self.g.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        self.g["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        self.g["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

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
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        c = self.g.register("CONDITION.1")
        self.g.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        self.g.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = self.g.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = self.g.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        self.g["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        self.g["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

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
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        c = self.g.register("CONDITION.1")
        self.g.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        self.g.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = self.g.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = self.g.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        self.g["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        self.g["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

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
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result1

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        c = self.g.register("CONDITION.1")
        self.g.register("TEST-STATEMENT-A", isa="EXE.BOOLEAN-STATEMENT")
        self.g.register("TEST-STATEMENT-B", isa="EXE.BOOLEAN-STATEMENT")
        b1 = self.g.register("TEST-STATEMENT-A.1", isa="TEST-STATEMENT-A")
        b2 = self.g.register("TEST-STATEMENT-B.1", isa="TEST-STATEMENT-B")
        self.g["TEST-STATEMENT-A"]["CLASSMAP"] = Literal(TestStatement1)
        self.g["TEST-STATEMENT-B"]["CLASSMAP"] = Literal(TestStatement2)

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
        gc = self.g.register("GOAL-CONDITION.1")
        self.assertTrue(Condition(gc).assess(None))

    def test_assess_with_varmap(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return varmap.resolve("X")

        c = self.g.register("CONDITION.1")
        b = self.g.register("BOOLEAN-STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")
        self.g["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        vm = self.g.register("VARMAP.1")
        v = self.g.register("VARIABLE.1")

        vm["WITH"] = Literal("X")
        vm["_WITH"] = v
        v["NAME"] = Literal("X")
        v["VALUE"] = True

        c["IF"] = b

        self.assertTrue(Condition(c).assess(VariableMap(vm)))


class PlanTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")

    def test_name(self):
        plan = self.g.register("PLAN.1")
        plan["NAME"] = Literal("Test Plan")

        self.assertEqual(Plan(plan).name(), "Test Plan")

    def test_is_negated(self):
        plan = self.g.register("PLAN.1")

        plan["NEGATE"] = False
        self.assertFalse(Plan(plan).is_negated())

        plan["NEGATE"] = True
        self.assertTrue(Plan(plan).is_negated())

    def test_select(self):
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        result = True

        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return result

        plan = self.g.register("PLAN.1")
        statement = self.g.register("BOOLEAN-STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")

        plan["SELECT"] = statement
        self.g["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        self.assertTrue(Plan(plan).select(None))

        result = False

        self.assertFalse(Plan(plan).select(None))

    def test_select_negated(self):
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return True

        self.g["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        statement = self.g.register("BOOLEAN-STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")

        plan = Plan.build(self.g, "test", statement, [])
        self.assertTrue(plan.select(None))

        plan = Plan.build(self.g, "test", statement, [], negate=True)
        self.assertFalse(plan.select(None))

    def test_select_with_variable(self):
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        class TestStatement(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
                return varmap.resolve("X")

        varmap = self.g.register("VARMAP.1")
        variable = self.g.register("VARIABLE.1")
        plan = self.g.register("PLAN.1")
        statement = self.g.register("BOOLEAN-STATEMENT.1", isa="EXE.BOOLEAN-STATEMENT")

        varmap["_WITH"] = variable
        variable["NAME"] = Literal("X")
        variable["VALUE"] = True
        plan["SELECT"] = statement
        self.g["BOOLEAN-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        self.assertTrue(Plan(plan).select(VariableMap(varmap)))

    def test_select_with_mp(self):
        from backend.models.mps import AgentMethod
        from backend.models.statement import MeaningProcedureStatement, MPRegistry

        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        class TestMP(AgentMethod):
            def run(self, var1):
                return var1

        MPRegistry.register(TestMP)

        mp_statement = MeaningProcedureStatement.instance(self.g, TestMP.__name__, ["$var1"])
        plan = Plan.build(self.g, "X", mp_statement, [])

        varmap = self.g.register("VARMAP.1")
        variable = self.g.register("VARIABLE.1")
        varmap["_WITH"] = variable
        variable["NAME"] = Literal("$var1")

        variable["VALUE"] = True
        self.assertTrue(plan.select(VariableMap(varmap)))

        variable["VALUE"] = False
        self.assertFalse(plan.select(VariableMap(varmap)))

    def test_select_when_default(self):
        plan = self.g.register("PLAN.1")
        plan["SELECT"] = Literal(Plan.DEFAULT)

        self.assertTrue(Plan(plan).select(None))

    def test_is_default(self):
        plan = self.g.register("PLAN.1")

        self.assertFalse(Plan(plan).is_default())

        plan["SELECT"] = Literal(Plan.DEFAULT)

        self.assertTrue(Plan(plan).is_default())

    def test_steps(self):
        plan = self.g.register("PLAN.1")

        step1 = self.g.register("STEP", generate_index=True)
        step2 = self.g.register("STEP", generate_index=True)

        step1["INDEX"] = 1
        step2["INDEX"] = 2

        self.assertEqual([], Plan(plan).steps())

        plan["HAS-STEP"] += step2
        plan["HAS-STEP"] += step1

        self.assertEqual([Step(step1), Step(step2)], Plan(plan).steps())

    def test_executed(self):
        g = Graph("TEST")

        step1 = Step.build(g, 1, [])
        step2 = Step.build(g, 2, [])

        plan = Plan.build(g, "test-plan", Plan.DEFAULT, [step1, step2])

        self.assertFalse(plan.executed())

        step1.frame["STATUS"] = Step.Status.FINISHED

        self.assertFalse(plan.executed())

        step2.frame["STATUS"] = Step.Status.FINISHED

        self.assertTrue(plan.executed())


class StepTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")

    def test_index(self):
        step = self.g.register("STEP")
        step["INDEX"] = 1

        self.assertEqual(1, Step(step).index())

    def test_status(self):
        step = self.g.register("STEP")

        step["STATUS"] = Step.Status.PENDING
        self.assertEqual(Step.Status.PENDING, Step(step).status())
        self.assertTrue(Step(step).is_pending())
        self.assertFalse(Step(step).is_finished())

        step["STATUS"] = Step.Status.FINISHED
        self.assertEqual(Step.Status.FINISHED, Step(step).status())
        self.assertFalse(Step(step).is_pending())
        self.assertTrue(Step(step).is_finished())

    def test_perform(self):
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        out = []

        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                nonlocal out
                out.append(self.frame["LOCAL"][0].resolve().value)

        step = self.g.register("STEP")
        statement1 = self.g.register("STATEMENT", generate_index=True, isa="EXE.STATEMENT")
        statement2 = self.g.register("STATEMENT", generate_index=True, isa="EXE.STATEMENT")

        self.g["STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        step["PERFORM"] = [statement1, statement2]
        statement1["LOCAL"] = Literal("X")
        statement2["LOCAL"] = Literal("Y")

        Step(step).perform(VariableMap(self.g.register("VARMAP")))

        self.assertEqual(out, ["X", "Y"])

    def test_perform_returns_outputs(self):
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                scope.outputs.append(123)

        agent = self.g.register("AGENT")
        goal = self.g.register("GOAL")
        plan = self.g.register("PLAN")
        step = self.g.register("STEP")

        statement = self.g.register("STATEMENT", generate_index=True, isa="EXE.STATEMENT")
        self.g["STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        step["PERFORM"] = [statement]

        outputs = Step(step).perform(VariableMap(self.g.register("VARMAP")))
        self.assertEqual([123], outputs)

    def test_perform_with_variables(self):
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        out = []

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                nonlocal out
                out.append(varmap.resolve("X"))

        step = self.g.register("STEP")
        statement = self.g.register("STATEMENT", generate_index=True, isa="EXE.STATEMENT")
        varmap = self.g.register("VARMAP")
        variable = self.g.register("VARIABLE")

        self.g["STATEMENT"]["CLASSMAP"] = Literal(TestStatement)
        step["PERFORM"] = statement
        varmap["_WITH"] = variable
        variable["NAME"] = Literal("X")
        variable["VALUE"] = 123

        Step(step).perform(VariableMap(varmap))

        self.assertEqual(out, [123])

    def test_perform_idle(self):
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        step = self.g.register("STEP")
        step["PERFORM"] = Literal(Step.IDLE)

        Step(step).perform(VariableMap(self.g.register("VARMAP")))

    def test_perform_raises_impasse_exceptions(self):
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        from backend.models.statement import AssertStatement, ExistsStatement

        perform = [AssertStatement.instance(self.g, ExistsStatement.instance(self.g, Frame.q(self.n).id("EXE.DNE")), [])]

        step = Step.build(self.g, 1, perform)

        with self.assertRaises(AssertStatement.ImpasseException):
            step.perform(VariableMap(self.g.register("VARMAP")))

        self.g.register("DNE")
        step.perform(VariableMap(self.g.register("VARMAP")))


class DecisionTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")
        self.n.register("OUTPUTS")

    def test_goal(self):
        goal = self.g.register("GOAL")

        decision = self.g.register("DECISION")
        decision["ON-GOAL"] = goal

        self.assertEqual(goal, Decision(decision).goal())

    def test_plan(self):
        plan = self.g.register("PLAN")

        decision = self.g.register("DECISION")
        decision["ON-PLAN"] = plan

        self.assertEqual(plan, Decision(decision).plan())

    def test_step(self):
        step = self.g.register("STEP")

        decision = self.g.register("DECISION")
        decision["ON-STEP"] = step

        self.assertEqual(step, Decision(decision).step())

    def test_impasses(self):
        decision = self.g.register("DECISION")

        self.assertEqual([], Decision(decision).impasses())

        impasse1 = self.g.register("GOAL", generate_index=True)
        impasse2 = self.g.register("GOAL", generate_index=True)

        decision["HAS-IMPASSE"] += impasse1
        decision["HAS-IMPASSE"] += impasse2

        self.assertEqual([impasse1, impasse2], Decision(decision).impasses())
        self.assertIsInstance(Decision(decision).impasses()[0], Goal)
        self.assertIsInstance(Decision(decision).impasses()[1], Goal)

    def test_outputs(self):
        decision = self.g.register("DECISION")

        self.assertEqual([], Decision(decision).outputs())

        output1 = self.g.register("XMR", generate_index=True)
        output2 = self.g.register("XMR", generate_index=True)

        decision["HAS-OUTPUT"] += output1
        decision["HAS-OUTPUT"] += output2

        self.assertEqual([output1, output2], Decision(decision).outputs())

    def test_priority(self):
        decision = self.g.register("DECISION")

        self.assertEqual(None, Decision(decision).priority())

        decision["HAS-PRIORITY"] = 0.5

        self.assertEqual(0.5, Decision(decision).priority())

    def test_cost(self):
        decision = self.g.register("DECISION")

        self.assertEqual(None, Decision(decision).cost())

        decision["HAS-COST"] = 0.5

        self.assertEqual(0.5, Decision(decision).cost())

    def test_requires(self):
        decision = self.g.register("DECISION")

        self.assertEqual([], Decision(decision).requires())

        capability1 = self.g.register("CAPABILITY", generate_index=True)
        capability2 = self.g.register("CAPABILITY", generate_index=True)

        output1 = self.g.register("OUTPUT-XMR", generate_index=True)
        output2 = self.g.register("OUTPUT-XMR", generate_index=True)

        output1["REQUIRES"] = capability1
        output2["REQUIRES"] = capability2

        decision["HAS-OUTPUT"] += output1
        decision["HAS-OUTPUT"] += output2

        self.assertEqual([capability1, capability2], Decision(decision).requires())

    def test_status(self):
        decision = self.g.register("DECISION")

        self.assertEqual(Decision.Status.PENDING, Decision(decision).status())

        decision["STATUS"] = Decision.Status.SELECTED

        self.assertEqual(Decision.Status.SELECTED, Decision(decision).status())

    def test_effectors(self):
        decision = self.g.register("DECISION")

        self.assertEqual([], Decision(decision).effectors())

        effector1 = self.g.register("EFFECTOR", generate_index=True)
        effector2 = self.g.register("EFFECTOR", generate_index=True)

        decision["HAS-EFFECTOR"] += effector1
        decision["HAS-EFFECTOR"] += effector2

        self.assertEqual([effector1, effector2], Decision(decision).effectors())

    def test_callbacks(self):
        decision = self.g.register("DECISION")

        self.assertEqual([], Decision(decision).callbacks())

        callback1 = self.g.register("CALLBACK", generate_index=True)
        callback2 = self.g.register("CALLBACK", generate_index=True)

        decision["HAS-CALLBACK"] += callback1
        decision["HAS-CALLBACK"] += callback2

        self.assertEqual([callback1, callback2], Decision(decision).callbacks())

    def test_build(self):
        goal = self.g.register("GOAL")
        plan = self.g.register("PLAN")
        step = self.g.register("STEP")

        decision = Decision.build(self.g, goal, plan, step)

        self.assertEqual(goal, decision.goal())
        self.assertEqual(plan, decision.plan())
        self.assertEqual(step, decision.step())
        self.assertEqual([], decision.outputs())
        self.assertEqual(None, decision.priority())
        self.assertEqual(None, decision.cost())
        self.assertEqual([], decision.requires())
        self.assertEqual(Decision.Status.PENDING, decision.status())
        self.assertEqual([], decision.callbacks())

    def test_generate_outputs(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        agent = self.g.register("AGENT")
        capability = self.g.register("CAPABILITY")

        template = OutputXMRTemplate.build(self.n, "test-template", OutputXMRTemplate.Type.PHYSICAL, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], agent)
        goal = Goal(self.g.register("GOAL"))
        step = Step.build(self.g, 1, statement)

        decision = Decision.build(self.g, goal, "TEST-PLAN", step)

        self.assertEqual([], decision.outputs())

        decision._generate_outputs()

        self.assertEqual([self.n.lookup("OUTPUTS.XMR.1")], decision.outputs())

    def test_generate_outputs_halts_and_registers_impasses(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import AssertStatement, ExistsStatement, MakeInstanceStatement, OutputXMRStatement, Variable

        self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

        Goal.define(self.g, "IMPASSE-GOAL", 0.5, 0.5, [], [], ["$var1"])

        resolution = MakeInstanceStatement.instance(self.g, self.g._namespace, "TEST.IMPASSE-GOAL", ["$var1"])
        statement1 = AssertStatement.instance(self.g, ExistsStatement.instance(self.g, Frame.q(self.n).id("EXE.DNE")), [resolution])

        template = OutputXMRTemplate.build(self.n, "test-template", OutputXMRTemplate.Type.PHYSICAL, None, [])
        statement2 = OutputXMRStatement.instance(self.g, template, [], None)

        goal = Goal(self.g.register("GOAL"))
        Variable.instance(self.g, "$var1", 123, goal)
        step = Step.build(self.g, 1, [statement1, statement2])
        decision = Decision.build(self.g, goal, "TEST-PLAN", step)

        self.assertEqual([], decision.impasses())
        self.assertEqual([], decision.outputs())
        self.assertEqual([], goal.subgoals())

        decision._generate_outputs()

        self.assertEqual(1, len(decision.impasses()))
        self.assertEqual("IMPASSE-GOAL", decision.impasses()[0].name())
        self.assertEqual("TEST.IMPASSE-GOAL.1", decision.impasses()[0].frame.name())
        self.assertEqual(123, decision.impasses()[0].resolve("$var1"))

        self.assertEqual("TEST.IMPASSE-GOAL.1", goal.subgoals()[0].frame.name())

        self.assertEqual(Decision.Status.BLOCKED, decision.status())

        self.assertEqual([], decision.outputs())

    def test_calculate_priority(self):
        definition = Goal.define(self.g, "TEST-GOAL", 1.0, 0.0, [], [], [])
        goal = Goal.instance_of(self.g, definition, [])

        decision = Decision.build(self.g, goal, "TEST.PLAN", "TEST.STEP")

        self.assertIsNone(decision.priority())

        decision._calculate_priority()

        self.assertEqual(1.0, decision.priority())

    def test_calculate_cost(self):
        definition = Goal.define(self.g, "TEST-GOAL", 0.0, 1.0, [], [], [])
        goal = Goal.instance_of(self.g, definition, [])

        decision = Decision.build(self.g, goal, "TEST.PLAN", "TEST.STEP")

        self.assertIsNone(decision.cost())

        decision._calculate_cost()

        self.assertEqual(1.0, decision.cost())

    def test_inspect(self):
        from unittest.mock import MagicMock

        decision = Decision(None)
        decision._generate_outputs = MagicMock()
        decision._calculate_priority = MagicMock()
        decision._calculate_cost = MagicMock()

        decision.inspect()
        decision._generate_outputs.assert_called_once()
        decision._calculate_priority.assert_called_once()
        decision._calculate_cost.assert_called_once()

    def test_select(self):
        decision = Decision.build(self.g, "TEST.GOAL", "TEST.PLAN", "TEST.STEP")
        self.assertEqual(Decision.Status.PENDING, decision.status())

        decision.select()
        self.assertEqual(Decision.Status.SELECTED, decision.status())

    def test_decline(self):
        decision = Decision.build(self.g, "TEST.GOAL", "TEST.PLAN", "TEST.STEP")
        self.assertEqual(Decision.Status.PENDING, decision.status())

        decision.decline()
        self.assertEqual(Decision.Status.DECLINED, decision.status())

    def test_execute(self):
        from backend.models.effectors import Capability, Effector
        from backend.models.mps import MPRegistry, OutputMethod
        from backend.models.output import OutputXMR, OutputXMRTemplate

        out = False

        class TestMP(OutputMethod):
            def run(self):
                nonlocal out
                out = True

        MPRegistry.register(TestMP)
        capability = Capability.instance(self.g, "CAPABILITY", "TestMP", ["ONT.EVENT"])
        output = OutputXMR.build(self.g, OutputXMRTemplate.Type.PHYSICAL, capability, "OUTPUT-XMR")

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")
        decision.frame["HAS-OUTPUT"] += output.frame

        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        effector.reserve(decision, output, capability)

        decision.execute(None, [effector])

        self.assertTrue(out)
        self.assertIn(effector, decision.effectors())
        self.assertEqual(Decision.Status.EXECUTING, decision.status())

    def test_creates_callback(self):
        from backend.models.effectors import Callback, Capability, Effector
        from backend.models.mps import MPRegistry, OutputMethod
        from backend.models.output import OutputXMR, OutputXMRTemplate

        class TestMP(OutputMethod):
            def run(self): pass

        MPRegistry.register(TestMP)
        capability = Capability.instance(self.g, "CAPABILITY", "TestMP", ["ONT.EVENT"])
        output = OutputXMR.build(self.g, OutputXMRTemplate.Type.PHYSICAL, capability, "OUTPUT-XMR")

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")
        decision.frame["HAS-OUTPUT"] += output.frame

        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        effector.reserve(decision, output, capability)

        decision.execute(None, [effector])

        callback = self.g["CALLBACK.1"]
        self.assertIn(callback, decision.callbacks())
        self.assertEqual(decision, Callback(callback).decision())
        self.assertEqual(effector, Callback(callback).effector())

    def test_callback_received(self):
        from backend.models.effectors import Callback, Capability, Effector
        from backend.models.mps import MPRegistry, OutputMethod
        from backend.models.output import OutputXMR, OutputXMRTemplate

        class TestMP(OutputMethod):
            def run(self): pass

        MPRegistry.register(TestMP)
        capability = Capability.instance(self.g, "CAPABILITY", "TestMP", ["ONT.EVENT"])
        output = OutputXMR.build(self.g, OutputXMRTemplate.Type.PHYSICAL, capability, "OUTPUT-XMR")

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")
        decision.frame["HAS-OUTPUT"] += output.frame

        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        effector.reserve(decision, output, capability)

        callback = Callback.build(self.g, decision, effector)

        decision.frame["HAS-EFFECTOR"] = effector.frame
        decision.frame["HAS-CALLBACK"] = callback.frame

        decision.callback_received(callback)
        self.assertNotIn(effector, decision.effectors())
        self.assertNotIn(callback, decision.callbacks())

    def test_assess_impasses(self):

        subgoal1 = self.g.register("GOAL", generate_index=True)
        subgoal1["STATUS"] = Goal.Status.ACTIVE

        subgoal2 = self.g.register("GOAL", generate_index=True)
        subgoal2["STATUS"] = Goal.Status.SATISFIED

        decision = self.g.register("DECISION")
        decision["HAS-IMPASSE"] += subgoal1
        decision["HAS-IMPASSE"] += subgoal2

        self.assertEqual([subgoal1, subgoal2], Decision(decision).impasses())

        Decision(decision).assess_impasses()

        self.assertEqual([subgoal1], Decision(decision).impasses())


class ExpectationTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")

        self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_status(self):
        e = self.g.register("EXPECTATION")
        e["STATUS"] = Expectation.Status.EXPECTING

        self.assertEqual(Expectation.Status.EXPECTING, Expectation(e).status())

    def test_condition(self):
        from backend.models.statement import ExistsStatement

        e = self.g.register("EXPECTATION")
        e["CONDITION"] = ExistsStatement.instance(self.g, Frame.q(self.n).id("TEST.FRAME.1")).frame

        self.assertEqual(ExistsStatement.instance(self.g, Frame.q(self.n).id("TEST.FRAME.1")), Expectation(e).condition())

    def test_build(self):
        from backend.models.statement import ExistsStatement

        e = Expectation.build(self.g, Expectation.Status.EXPECTING, ExistsStatement.instance(self.g, Frame.q(self.n).id("TEST.FRAME.1")))

        self.assertEqual(Expectation.Status.EXPECTING, e.status())
        self.assertEqual(ExistsStatement.instance(self.g, Frame.q(self.n).id("TEST.FRAME.1")), e.condition())