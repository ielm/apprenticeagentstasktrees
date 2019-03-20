from backend.agent import Agent
from backend.models.agenda import Agenda, Condition, Decision, Effect, Expectation, Goal, Plan, Step, Trigger
# from backend.models.bootstrap import Bootstrap
# from backend.models.graph import Frame, Graph, Literal, Network
from backend.models.statement import Statement, StatementRegistry, StatementScope, VariableMap
from backend.models.xmr import XMR
from backend.utils.AgentOntoLang import AgentOntoLang
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Query import ExistsComparator, IdComparator, IsAComparator, Query
from ontograph.Space import Space

import unittest


class AgendaTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_goals(self):
        f1 = Frame("@TEST.AGENDA.1")  # Typically the agent identity frame (so, e.g., ROBOT.1) is used, as there is no "AGENDA".
        g1 = Frame("@TEST.GOAL.1")
        g2 = Frame("@TEST.GOAL.2")
        g3 = Frame("@TEST.GOAL.3")
        g4 = Frame("@TEST.GOAL.4")

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
        f1 = Frame("@TEST.AGENDA.1")
        g1 = Frame("@TEST.GOAL.1")
        g2 = Frame("@TEST.GOAL.2")

        agenda = Agenda(f1)
        agenda.add_goal(g1)
        agenda.add_goal(Goal(g2))

        self.assertEqual(agenda.goals(pending=True), [Goal(g1), Goal(g2)])

    def test_prepare_plan(self):
        f1 = Frame("@TEST.AGENDA.1")
        a1 = Frame("@TEST.PLAN.1")
        a2 = Frame("@TEST.PLAN.2")

        agenda = Agenda(f1)

        agenda.prepare_plan(a1)
        self.assertEqual(len(f1["PLAN-TO-TAKE"]), 1)
        self.assertEqual(f1["PLAN-TO-TAKE"][0], a1)

        agenda.prepare_plan(Plan(a2))
        self.assertEqual(len(f1["PLAN-TO-TAKE"]), 2)
        self.assertEqual(f1["PLAN-TO-TAKE"][0], a1)
        self.assertEqual(f1["PLAN-TO-TAKE"][1], a2)

    def test_plan(self):
        f1 = Frame("@TEST.AGENDA.1")
        a1 = Frame("@TEST.PLAN.1")

        f1["PLAN-TO-TAKE"] = a1

        agenda = Agenda(f1)
        self.assertEqual([a1], agenda.plan())

    def test_triggers(self):
        space = Space("TEST")

        agenda = Frame("@TEST.AGENDA")
        definition = Frame("@TEST.MYGOAL")

        query1 = Query(IsAComparator("@TEST.TEST.?"))
        query2 = Query(IsAComparator("@TEST.TEST.?"))

        trigger1 = Trigger.build(space, query1, definition)
        trigger2 = Trigger.build(space, query2, definition)

        agenda["TRIGGER"] += trigger1.frame
        agenda["TRIGGER"] += trigger2.frame

        self.assertEqual([trigger1, trigger2], Agenda(agenda).triggers())

    def test_add_trigger(self):
        agenda = Frame("@TEST.AGENDA")
        definition = Frame("@TEST.MYGOAL")

        query = Query(IsAComparator("@TEST.TEST.?"))

        trigger = Trigger.build(Space("TEST"), query, definition)

        Agenda(agenda).add_trigger(trigger)

        self.assertEqual([trigger], Agenda(agenda).triggers())

    def test_fire_triggers(self):
        space = Space("TEST")

        agenda = Agenda(Frame("@TEST.AGENDA"))

        definition = Frame("@TEST.MYGOAL")
        definition["WITH"] = "$var1"

        query = Query(IdComparator("@TEST.TARGET.1"))

        trigger1 = Trigger.build(space, query, definition)
        agenda.add_trigger(trigger1)

        trigger2 = Trigger.build(space, query, definition)
        agenda.add_trigger(trigger2)

        target = Frame("@TEST.TARGET.1")

        self.assertEqual(0, len(agenda.goals(pending=True, active=True)))

        agenda.fire_triggers()

        self.assertIn(Frame("@TEST.GOAL.1"), agenda.goals(pending=True, active=True))
        self.assertEqual(target, Goal(Frame("@TEST.GOAL.1")).resolve("$var1"))

        self.assertIn(Frame("@TEST.GOAL.2"), agenda.goals(pending=True, active=True))
        self.assertEqual(target, Goal(Frame("@TEST.GOAL.2")).resolve("$var1"))


class GoalTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_name(self):
        f = Frame("@TEST.TEST.1")
        f["NAME"] = "Test Name"

        goal = Goal(f)
        self.assertEqual(goal.name(), "Test Name")

    def test_status_from_frame(self):
        f = Frame("@TEST.TEST.1")
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
        f = Frame("@TEST.TEST.1")
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
        s = Space("TEST")

        step1 = Step.build(s, 1, [])
        step2 = Step.build(s, 1, [])

        plan1 = Plan.build(s, "test-plan-1", Plan.DEFAULT, [step1])
        plan2 = Plan.build(s, "test-plan-2", Plan.DEFAULT, [step2])

        goal = Frame("@TEST.GOAL.1")
        goal["PLAN"] = [plan1.frame, plan2.frame]

        self.assertFalse(Goal(goal).executed())

        step1.frame["STATUS"] = Step.Status.FINISHED

        self.assertTrue(Goal(goal).executed())

    def test_priority_numeric(self):

        f = Frame("@TEST.GOAL.1")
        f["PRIORITY"] = 0.5

        goal = Goal(f)
        self.assertEqual(goal.priority(), 0.5)
        self.assertTrue(f["_PRIORITY"] == 0.5)

    def test_priority_calculation(self):
        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return 0.5

        StatementRegistry.register(TestStatement)

        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        Frame("@EXE.RETURNING-STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
        statement = Frame("@TEST.STATEMENT.1").add_parent("@EXE.RETURNING-STATEMENT")

        f = Frame("@TEST.GOAL.1")
        f["PRIORITY"] = statement

        goal = Goal(f)
        self.assertEqual(goal.priority(), 0.5)
        self.assertTrue(f["_PRIORITY"] == 0.5)

    def test_priority(self):
        f = Frame("@TEST.GOAL.1")

        goal = Goal(f)
        self.assertEqual(0.0, goal.priority())
        self.assertTrue(f["_PRIORITY"] == 0.0)

    def test_cached_priority(self):
        f = Frame("@TEST.GOAL.1")

        goal = Goal(f)
        self.assertEqual(0.0, goal._cached_priority())
        self.assertEqual(0.0, goal.priority())
        self.assertEqual(0.0, goal._cached_priority())

    def test_resources_numeric(self):

        f = Frame("@TEST.GOAL.1")
        f["RESOURCES"] = 0.5

        goal = Goal(f)
        self.assertEqual(goal.resources(), 0.5)
        self.assertTrue(f["_RESOURCES"] == 0.5)

    def test_resources_calculation(self):
        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return 0.5

        StatementRegistry.register(TestStatement)

        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        Frame("@EXE.RETURNING-STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
        statement = Frame("@TEST.STATEMENT.1").add_parent("@EXE.RETURNING-STATEMENT")

        f = Frame("@TEST.GOAL.1")
        f["RESOURCES"] = statement

        goal = Goal(f)
        self.assertEqual(goal.resources(), 0.5)
        self.assertTrue(f["_RESOURCES"] == 0.5)

    def test_resources(self):
        f = Frame("@TEST.GOAL.1")

        goal = Goal(f)
        self.assertEqual(1.0, goal.resources())
        self.assertTrue(f["_RESOURCES"] == 1.0)

    def test_cached_resources(self):
        f = Frame("@TEST.GOAL.1")

        goal = Goal(f)
        self.assertEqual(1.0, goal._cached_resources())
        self.assertEqual(1.0, goal.resources())
        self.assertEqual(1.0, goal._cached_resources())

    def test_assign_decision(self):
        f = Frame("@TEST.GOAL.1")
        goal = Goal(f)
        goal.decision(decide=0.5)
        self.assertTrue(0.5 in f["_DECISION"])

    def test_cached_decision(self):
        f = Frame("@TEST.GOAL.1")

        goal = Goal(f)
        self.assertEqual(0.0, goal.decision())

        f["_DECISION"] = 0.5
        self.assertEqual(0.5, goal.decision())

    def test_plan(self):
        goal = Frame("@TEST.GOAL.1")
        plan1 = Frame("@TEST.PLAN.1")
        plan2 = Frame("@TEST.PLAN.2")

        goal["PLAN"] = [plan1, plan2]
        plan2["SELECT"] = Plan.DEFAULT

        self.assertEqual(Goal(goal).plan(), plan2)
        self.assertIsInstance(Goal(goal).plan(), Plan)

    def test_assess(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return True

        StatementRegistry.register(TestStatement)

        class TestAgent(Agent):
            def __init__(self):
                pass

        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        goal = Frame("@TEST.GOAL.1")
        condition1 = Frame("@TEST.CONDITION.1")
        condition2 = Frame("@TEST.CONDITION.2")
        statement = Frame("@TEST.STATEMENT.1").add_parent("@EXE.BOOLEAN-STATEMENT")

        Frame("@EXE.BOOLEAN-STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
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
        subgoal1 = Frame("@TEST.SUBGOAL.1")
        subgoal1["STATUS"] = Goal.Status.ACTIVE

        subgoal2 = Frame("@TEST.SUBGOAL.2")
        subgoal2["STATUS"] = Goal.Status.SATISFIED

        goal = Frame("@TEST.GOAL.1")
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
        subgoal1 = Frame("@TEST.SUBGOAL.1")
        subgoal1["STATUS"] = Goal.Status.ACTIVE

        subgoal2 = Frame("@TEST.SUBGOAL.2")
        subgoal2["STATUS"] = Goal.Status.SATISFIED

        goal = Frame("@TEST.GOAL.1")
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
        definition = Frame("@TEST.GOAL-DEF")
        plan = Frame("@TEST.PLAN.1")
        condition = Frame("@TEST.CONDITION.1")

        plan["SELECT"] = Plan.DEFAULT

        definition["NAME"] = "Test Goal"
        definition["PRIORITY"] = 0.5
        definition["PLAN"] = plan
        definition["WHEN"] = condition
        definition["WITH"] = "VAR_X"

        params = [123]
        goal = Goal.instance_of(Space("TEST"), definition, params)

        self.assertEqual(goal.name(), "Test Goal")
        self.assertTrue(goal.frame["PRIORITY"] == 0.5)
        self.assertTrue(goal.frame["PLAN"] == plan)
        self.assertTrue(goal.frame["WHEN"] == condition)
        self.assertTrue(goal.frame["WITH"] == "VAR_X")
        self.assertEqual(1, len(goal.frame["_WITH"]))

        var = goal.frame["_WITH"][0]
        self.assertEqual(var["NAME"], "VAR_X")
        self.assertEqual(var["FROM"], goal.frame)
        self.assertEqual(var["VALUE"], 123)

    def test_effects(self):
        goal = Frame("@TEST.GOAL.1")

        from backend.models.statement import AddFillerStatement

        statement1 = AddFillerStatement.instance(Space("TEST"), "@TEST.FRAME.1", "SLOT", 123)
        statement2 = AddFillerStatement.instance(Space("TEST"), "@TEST.FRAME.1", "SLOT", "$var1")

        effect1 = Effect.build(Space("TEST"), [statement1])
        effect2 = Effect.build(Space("TEST"), [statement2])

        goal["HAS-EFFECT"] += effect1.frame
        goal["HAS-EFFECT"] += effect2.frame

        self.assertEqual([effect1, effect2], Goal(goal).effects())

    def test_effects_applied_in_assess_if_goal_satisfied(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        goal = Frame("@TEST.GOAL.1")

        from backend.models.statement import AddFillerStatement, Variable

        frame = Frame("@TEST.FRAME.?")

        statement1 = AddFillerStatement.instance(Space("TEST"), "@TEST.FRAME.1", "SLOT", 123)
        statement2 = AddFillerStatement.instance(Space("TEST"), "@TEST.FRAME.1", "SLOT", "$var1")

        effect1 = Effect.build(Space("TEST"), [statement1])
        effect2 = Effect.build(Space("TEST"), [statement2])

        goal["HAS-EFFECT"] += effect1.frame
        goal["HAS-EFFECT"] += effect2.frame

        Variable.instance(Space("TEST"), "$var1", 456, Goal(goal))

        goal["STATUS"] = Goal.Status.ACTIVE
        Goal(goal).assess()
        self.assertEqual([], frame["SLOT"])

        goal["STATUS"] = Goal.Status.SATISFIED
        Goal(goal).assess()
        self.assertEqual([123, 456], frame["SLOT"])


class TriggerTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_query(self):

        query = Query(IdComparator("@TEST.FRAME.123"))

        trigger = Frame("@TEST.TRIGGER")
        trigger["QUERY"] = query

        self.assertEqual(query, Trigger(trigger).query())

    def test_definition(self):
        goal = Frame("@TEST.MYGOAL")
        trigger = Frame("@TEST.TRIGGER")
        trigger["DEFINITION"] = goal

        self.assertEqual(goal, Trigger(trigger).definition())

    def test_triggered_on(self):
        o1 = Frame("@TEST.OBJECT.1")
        o2 = Frame("@TEST.OBJECT.2")

        trigger = Frame("@TEST.TRIGGER")

        trigger["TRIGGERED-ON"] += o1
        trigger["TRIGGERED-ON"] += o2

        self.assertEqual([o1, o2], Trigger(trigger).triggered_on())

    def test_fire_creates_goal_instance(self):
        agenda = Agenda(Frame("@TEST.AGENDA"))

        definition = Frame("@TEST.MYGOAL")
        definition["WITH"] = "$var1"

        trigger = Trigger.build(Space("TEST"), Query(IdComparator("@TEST.TARGET.1")), definition)
        agenda.add_trigger(trigger)

        target = Frame("@TEST.TARGET.?")

        self.assertEqual(0, len(agenda.goals(pending=True, active=True)))

        trigger.fire(agenda)

        self.assertIn(Frame("@TEST.GOAL.1"), agenda.goals(pending=True, active=True))
        self.assertEqual(target, Goal(Frame("@TEST.GOAL.1")).resolve("$var1"))

    def test_fire_creates_multiple_goal_instances(self):
        agenda = Agenda(Frame("@TEST.AGENDA"))

        definition = Frame("@TEST.MYGOAL")
        definition["WITH"] = "$var1"

        trigger = Trigger.build(Space("TEST"), Query(ExistsComparator(slot="MYSLOT")), definition)

        target1 = Frame("@TEST.TARGET.?")
        target1["MYSLOT"] = 123

        target2 = Frame("@TEST.TARGET.?")
        target2["MYSLOT"] = 123

        self.assertEqual(0, len(agenda.goals(pending=True, active=True)))

        trigger.fire(agenda)

        self.assertIn(Frame("@TEST.GOAL.1"), agenda.goals(pending=True, active=True))
        self.assertIn(Frame("@TEST.GOAL.2"), agenda.goals(pending=True, active=True))

        resolved = [Goal(Frame("@TEST.GOAL.1")).resolve("$var1"), Goal(Frame("@TEST.GOAL.2")).resolve("$var1")]
        self.assertEqual(2, len(resolved))
        self.assertIn(target1, resolved)
        self.assertIn(target2, resolved)

    def test_fire_filters_existing_triggered_instances(self):
        agenda = Agenda(Frame("@TEST.AGENDA"))

        definition = Frame("@TEST.MYGOAL")
        definition["WITH"] = "$var1"

        trigger = Trigger.build(Space("TEST"), Query(ExistsComparator(slot="MYSLOT")), definition)

        target1 = Frame("@TEST.TARGET.?")
        target1["MYSLOT"] = 123

        self.assertEqual(0, len(agenda.goals(pending=True, active=True)))

        trigger.fire(agenda)

        self.assertIn(Frame("@TEST.GOAL.1"), agenda.goals(pending=True, active=True))
        self.assertEqual(target1, Goal(Frame("@TEST.GOAL.1")).resolve("$var1"))

        target2 = Frame("@TEST.TARGET.?")
        target2["MYSLOT"] = 123

        trigger.fire(agenda)

        self.assertIn(Frame("@TEST.GOAL.2"), agenda.goals(pending=True, active=True))
        self.assertEqual(target2, Goal(Frame("@TEST.GOAL.2")).resolve("$var1"))

        self.assertEqual(2, len(agenda.goals(pending=True, active=True)))


class ConditionTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

    def test_order(self):
        gc = Frame("@TEST.CONDITION.1")
        gc["ORDER"] = 1

        self.assertEqual(Condition(gc).order(), 1)

    def test_status(self):
        gc = Frame("@TEST.GOAL-CONDITION.1")
        gc["STATUS"] = Goal.Status.SATISFIED.name

        self.assertEqual(Condition(gc).status(), Goal.Status.SATISFIED)

    def test_on(self):
        gc = Frame("@TEST.GOAL-CONDITION.1")
        gc["ON"] = Condition.On.EXECUTED

        self.assertEqual(Condition(gc).on(), Condition.On.EXECUTED)

    def test_requires_boolean_statement(self):
        c = Frame("@TEST.CONDITION.1")
        b = Frame("@TEST.STATEMENT.1").add_parent("@EXE.STATEMENT")

        c["IF"] = b

        with self.assertRaises(Exception):
            Condition(c)

    def test_assess_executed(self):
        goal = Frame("@TEST.GOAL")

        condition = Frame("@TEST.CONDITION")
        condition["ON"] = Condition.On.EXECUTED

        self.assertFalse(Condition(condition).assess(VariableMap(goal)))

        goal["PLAN"] = Frame("@TEST.PLAN")

        self.assertTrue(Condition(condition).assess(VariableMap(goal)))

    def test_assess_if(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return True

        StatementRegistry.register(TestStatement)

        c = Frame("@TEST.CONDITION.1")
        b = Frame("@TEST.BOOLEAN-STATEMENT.1").add_parent("@EXE.BOOLEAN-STATEMENT")
        Frame("@EXE.BOOLEAN-STATEMENT")["CLASSMAP"] = TestStatement.__qualname__

        c["IF"] = b

        self.assertTrue(Condition(c)._assess_if(b, None))

    def test_assess_and(self):

        result1 = True
        result2 = True

        class TestStatement1(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
                return result1

        StatementRegistry.register(TestStatement1)

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        StatementRegistry.register(TestStatement2)

        c = Frame("@TEST.CONDITION.1")
        Frame("@TEST.STATEMENT-A").add_parent("@EXE.BOOLEAN-STATEMENT")
        Frame("@TEST.STATEMENT-B").add_parent("@EXE.BOOLEAN-STATEMENT")
        b1 = Frame("@TEST.STATEMENT-A.1").add_parent("@TEST.STATEMENT-A")
        b2 = Frame("@TEST.STATEMENT-B.1").add_parent("@TEST.STATEMENT-B")
        Frame("@TEST.STATEMENT-A")["CLASSMAP"] = TestStatement1.__qualname__
        Frame("@TEST.STATEMENT-B")["CLASSMAP"] = TestStatement2.__qualname__

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

        StatementRegistry.register(TestStatement1)

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        StatementRegistry.register(TestStatement2)

        c = Frame("@TEST.CONDITION.1")
        Frame("@TEST.STATEMENT-A").add_parent("@EXE.BOOLEAN-STATEMENT")
        Frame("@TEST.STATEMENT-B").add_parent("@EXE.BOOLEAN-STATEMENT")
        b1 = Frame("@TEST.STATEMENT-A.1").add_parent("@TEST.STATEMENT-A")
        b2 = Frame("@TEST.STATEMENT-B.1").add_parent("@TEST.STATEMENT-B")
        Frame("@TEST.STATEMENT-A")["CLASSMAP"] = TestStatement1.__qualname__
        Frame("@TEST.STATEMENT-B")["CLASSMAP"] = TestStatement2.__qualname__

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

        StatementRegistry.register(TestStatement1)

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        StatementRegistry.register(TestStatement2)

        c = Frame("@TEST.CONDITION.1")
        Frame("@TEST.STATEMENT-A").add_parent("@EXE.BOOLEAN-STATEMENT")
        Frame("@TEST.STATEMENT-B").add_parent("@EXE.BOOLEAN-STATEMENT")
        b1 = Frame("@TEST.STATEMENT-A.1").add_parent("@TEST.STATEMENT-A")
        b2 = Frame("@TEST.STATEMENT-B.1").add_parent("@TEST.STATEMENT-B")
        Frame("@TEST.STATEMENT-A")["CLASSMAP"] = TestStatement1.__qualname__
        Frame("@TEST.STATEMENT-B")["CLASSMAP"] = TestStatement2.__qualname__

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

        StatementRegistry.register(TestStatement1)

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        StatementRegistry.register(TestStatement2)

        c = Frame("@TEST.CONDITION.1")
        Frame("@TEST.STATEMENT-A").add_parent("@EXE.BOOLEAN-STATEMENT")
        Frame("@TEST.STATEMENT-B").add_parent("@EXE.BOOLEAN-STATEMENT")
        b1 = Frame("@TEST.STATEMENT-A.1").add_parent("@TEST.STATEMENT-A")
        b2 = Frame("@TEST.STATEMENT-B.1").add_parent("@TEST.STATEMENT-B")
        Frame("@TEST.STATEMENT-A")["CLASSMAP"] = TestStatement1.__qualname__
        Frame("@TEST.STATEMENT-B")["CLASSMAP"] = TestStatement2.__qualname__

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

        StatementRegistry.register(TestStatement1)

        class TestStatement2(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return result2

        StatementRegistry.register(TestStatement2)

        c = Frame("@TEST.CONDITION.1")
        Frame("@TEST.STATEMENT-A").add_parent("@EXE.BOOLEAN-STATEMENT")
        Frame("@TEST.STATEMENT-B").add_parent("@EXE.BOOLEAN-STATEMENT")
        b1 = Frame("@TEST.STATEMENT-A.1").add_parent("@TEST.STATEMENT-A")
        b2 = Frame("@TEST.STATEMENT-B.1").add_parent("@TEST.STATEMENT-B")
        Frame("@TEST.STATEMENT-A")["CLASSMAP"] = TestStatement1.__qualname__
        Frame("@TEST.STATEMENT-B")["CLASSMAP"] = TestStatement2.__qualname__

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
        gc = Frame("@TEST.GOAL-CONDITION.1")
        self.assertTrue(Condition(gc).assess(None))

    def test_assess_with_varmap(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope,  varmap: VariableMap):
                return varmap.resolve("X")

        StatementRegistry.register(TestStatement)

        c = Frame("@TEST.CONDITION.1")
        b = Frame("@TEST.BOOLEAN-STATEMENT.1").add_parent("@EXE.BOOLEAN-STATEMENT")
        Frame("@EXE.BOOLEAN-STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
        vm = Frame("@TEST.VARMAP.1")
        v = Frame("@TEST.VARIABLE.1")

        vm["WITH"] = "X"
        vm["_WITH"] = v
        v["NAME"] = "X"
        v["VALUE"] = True

        c["IF"] = b

        self.assertTrue(Condition(c).assess(VariableMap(vm)))


class PlanTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_name(self):
        plan = Frame("@TEST.PLAN.1")
        plan["NAME"] = "Test Plan"

        self.assertEqual(Plan(plan).name(), "Test Plan")

    def test_is_negated(self):
        plan = Frame("@TEST.PLAN.1")

        plan["NEGATE"] = False
        self.assertFalse(Plan(plan).is_negated())

        plan["NEGATE"] = True
        self.assertTrue(Plan(plan).is_negated())

    def test_select(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        result = True

        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return result

        StatementRegistry.register(TestStatement)

        plan = Frame("@TEST.PLAN.1")
        statement = Frame("@TEST.BOOLEAN-STATEMENT.1").add_parent("@EXE.BOOLEAN-STATEMENT")

        plan["SELECT"] = statement
        Frame("@EXE.BOOLEAN-STATEMENT")["CLASSMAP"] = TestStatement.__qualname__

        self.assertTrue(Plan(plan).select(None))

        result = False

        self.assertFalse(Plan(plan).select(None))

    def test_select_negated(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                return True

        StatementRegistry.register(TestStatement)

        Frame("@EXE.BOOLEAN-STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
        statement = Frame("@TEST.BOOLEAN-STATEMENT.1").add_parent("@EXE.BOOLEAN-STATEMENT")

        plan = Plan.build(Space("TEST"), "test", statement, [])
        self.assertTrue(plan.select(None))

        plan = Plan.build(Space("TEST"), "test", statement, [], negate=True)
        self.assertFalse(plan.select(None))

    def test_select_with_variable(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        class TestStatement(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
                return varmap.resolve("X")

        StatementRegistry.register(TestStatement)

        varmap = Frame("@TEST.VARMAP.1")
        variable = Frame("@TEST.VARIABLE.1")
        plan = Frame("@TEST.PLAN.1")
        statement = Frame("@TEST.BOOLEAN-STATEMENT.1").add_parent("@EXE.BOOLEAN-STATEMENT")

        varmap["_WITH"] = variable
        variable["NAME"] = "X"
        variable["VALUE"] = True
        plan["SELECT"] = statement
        Frame("@EXE.BOOLEAN-STATEMENT")["CLASSMAP"] = TestStatement.__qualname__

        self.assertTrue(Plan(plan).select(VariableMap(varmap)))

    def test_select_with_mp(self):
        from backend.models.mps import AgentMethod
        from backend.models.statement import MeaningProcedureStatement, MPRegistry

        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        class TestMP(AgentMethod):
            def run(self, var1):
                return var1

        MPRegistry.register(TestMP)

        mp_statement = MeaningProcedureStatement.instance(Space("TEST"), TestMP.__name__, ["$var1"])
        plan = Plan.build(Space("TEST"), "X", mp_statement, [])

        varmap = Frame("@TEST.VARMAP.1")
        variable = Frame("@TEST.VARIABLE.1")
        varmap["_WITH"] = variable
        variable["NAME"] = "$var1"

        variable["VALUE"] = True
        self.assertTrue(plan.select(VariableMap(varmap)))

        variable["VALUE"] = False
        self.assertFalse(plan.select(VariableMap(varmap)))

    def test_select_when_default(self):
        plan = Frame("@TEST.PLAN.1")
        plan["SELECT"] = Plan.DEFAULT

        self.assertTrue(Plan(plan).select(None))

    def test_is_default(self):
        plan = Frame("@TEST.PLAN.1")

        self.assertFalse(Plan(plan).is_default())

        plan["SELECT"] = Plan.DEFAULT

        self.assertTrue(Plan(plan).is_default())

    def test_steps(self):
        plan = Frame("@TEST.PLAN.1")

        step1 = Frame("@TEST.STEP.?")
        step2 = Frame("@TEST.STEP.?")

        step1["INDEX"] = 1
        step2["INDEX"] = 2

        self.assertEqual([], Plan(plan).steps())

        plan["HAS-STEP"] += step2
        plan["HAS-STEP"] += step1

        self.assertEqual([Step(step1), Step(step2)], Plan(plan).steps())

    def test_executed(self):
        s = Space("TEST")

        step1 = Step.build(s, 1, [])
        step2 = Step.build(s, 2, [])

        plan = Plan.build(s, "test-plan", Plan.DEFAULT, [step1, step2])

        self.assertFalse(plan.executed())

        step1.frame["STATUS"] = Step.Status.FINISHED

        self.assertFalse(plan.executed())

        step2.frame["STATUS"] = Step.Status.FINISHED

        self.assertTrue(plan.executed())


class StepTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        StatementRegistry.reset()

    def test_index(self):
        step = Frame("@TEST.STEP")
        step["INDEX"] = 1

        self.assertEqual(1, Step(step).index())

    def test_status(self):
        step = Frame("@TEST.STEP")

        step["STATUS"] = Step.Status.PENDING
        self.assertEqual(Step.Status.PENDING, Step(step).status())
        self.assertTrue(Step(step).is_pending())
        self.assertFalse(Step(step).is_finished())

        step["STATUS"] = Step.Status.FINISHED
        self.assertEqual(Step.Status.FINISHED, Step(step).status())
        self.assertFalse(Step(step).is_pending())
        self.assertTrue(Step(step).is_finished())

    def test_perform(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        out = []

        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                nonlocal out
                out.append(self.frame["LOCAL"][0])

        StatementRegistry.register(TestStatement)

        step = Frame("@TEST.STEP")
        statement1 = Frame("@TEST.STATEMENT.?").add_parent("@EXE.STATEMENT")
        statement2 = Frame("@TEST.STATEMENT.?").add_parent("@EXE.STATEMENT")

        Frame("@EXE.STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
        step["PERFORM"] = [statement1, statement2]
        statement1["LOCAL"] = "X"
        statement2["LOCAL"] = "Y"

        Step(step).perform(VariableMap(Frame("@TEST.VARMAP")))

        self.assertEqual(out, ["X", "Y"])

    def test_perform_returns_scope_with_outputs(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                scope.outputs.append(123)

        StatementRegistry.register(TestStatement)

        agent = Frame("@TEST.AGENT")
        goal = Frame("@TEST.GOAL")
        plan = Frame("@TEST.PLAN")
        step = Frame("@TEST.STEP")

        statement = Frame("@TEST.STATEMENT.?").add_parent("@EXE.STATEMENT")
        Frame("@EXE.STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
        step["PERFORM"] = [statement]

        scope = Step(step).perform(VariableMap(Frame("@TEST.VARMAP")))
        self.assertEqual([123], scope.outputs)

    def test_perform_returns_scope_with_expectations(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                scope.expectations.append(123)

        StatementRegistry.register(TestStatement)

        agent = Frame("@TEST.AGENT")
        goal = Frame("@TEST.GOAL")
        plan = Frame("@TEST.PLAN")
        step = Frame("@TEST.STEP")

        statement = Frame("@TEST.STATEMENT.?").add_parent("@EXE.STATEMENT")
        Frame("@EXE.STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
        step["PERFORM"] = [statement]

        scope = Step(step).perform(VariableMap(Frame("@TEST.VARMAP")))
        self.assertEqual([123], scope.expectations)

    def test_perform_with_transients_overrides_scope_detection(self):
        from backend.models.statement import TransientFrame

        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        transient: Frame = None

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                nonlocal transient
                transient = Frame("@" + self.frame.space().name + ".TRANSIENT")
                scope.transients.append(TransientFrame(transient))

        StatementRegistry.register(TestStatement)

        agent = Frame("@TEST.AGENT")
        goal = Frame("@TEST.GOAL")
        plan = Frame("@TEST.PLAN")
        step = Frame("@TEST.STEP")

        statement = Frame("@TEST.STATEMENT.?").add_parent("@EXE.STATEMENT")
        Frame("@EXE.STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
        step["PERFORM"] = [statement]

        Step(step).perform(VariableMap(Frame("@TEST.VARMAP")))

        step["STATUS"] = Step.Status.PENDING
        self.assertTrue(TransientFrame(transient).is_in_scope())

        step["STATUS"] = Step.Status.FINISHED
        self.assertFalse(TransientFrame(transient).is_in_scope())

    def test_perform_with_variables(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        out = []

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                nonlocal out
                out.append(varmap.resolve("X"))

        StatementRegistry.register(TestStatement)

        step = Frame("@TEST.STEP")
        statement = Frame("@TEST.STATEMENT.?").add_parent("@EXE.STATEMENT")
        varmap = Frame("@TEST.VARMAP")
        variable = Frame("@TEST.VARIABLE")

        Frame("@EXE.STATEMENT")["CLASSMAP"] = TestStatement.__qualname__
        step["PERFORM"] = statement
        varmap["_WITH"] = variable
        variable["NAME"] = "X"
        variable["VALUE"] = 123

        Step(step).perform(VariableMap(varmap))

        self.assertEqual(out, [123])

    def test_perform_idle(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        step = Frame("@TEST.STEP")
        step["PERFORM"] = Step.IDLE

        Step(step).perform(VariableMap(Frame("@TEST.VARMAP")))

    def test_perform_raises_impasse_exceptions(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        from backend.models.statement import AssertStatement, ExistsStatement

        perform = [AssertStatement.instance(Space("TEST"), ExistsStatement.instance(Space("TEST"), Query(IdComparator("@EXE.DNE"))), [])]

        step = Step.build(Space("TEST"), 1, perform)

        with self.assertRaises(AssertStatement.ImpasseException):
            step.perform(VariableMap(Frame("@TEST.VARMAP")))

        Frame("@EXE.DNE")
        step.perform(VariableMap(Frame("@TEST.VARMAP")))


class DecisionTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_goal(self):
        goal = Frame("@TEST.GOAL")

        decision = Frame("@TEST.DECISION")
        decision["ON-GOAL"] = goal

        self.assertEqual(goal, Decision(decision).goal())

    def test_plan(self):
        plan = Frame("@TEST.PLAN")

        decision = Frame("@TEST.DECISION")
        decision["ON-PLAN"] = plan

        self.assertEqual(plan, Decision(decision).plan())

    def test_step(self):
        step = Frame("@TEST.STEP")

        decision = Frame("@TEST.DECISION")
        decision["ON-STEP"] = step

        self.assertEqual(step, Decision(decision).step())

    def test_impasses(self):
        decision = Frame("@TEST.DECISION")

        self.assertEqual([], Decision(decision).impasses())

        impasse1 = Frame("@TEST.GOAL.?")
        impasse2 = Frame("@TEST.GOAL.?")

        decision["HAS-IMPASSE"] += impasse1
        decision["HAS-IMPASSE"] += impasse2

        self.assertEqual([impasse1, impasse2], Decision(decision).impasses())
        self.assertIsInstance(Decision(decision).impasses()[0], Goal)
        self.assertIsInstance(Decision(decision).impasses()[1], Goal)

    def test_outputs(self):
        decision = Frame("@TEST.DECISION")

        self.assertEqual([], Decision(decision).outputs())

        output1 = Frame("@TEST.XMR.?")
        output2 = Frame("@TEST.XMR.?")

        decision["HAS-OUTPUT"] += output1
        decision["HAS-OUTPUT"] += output2

        self.assertEqual([output1, output2], Decision(decision).outputs())

    def test_expectations(self):
        decision = Frame("@TEST.DECISION")

        self.assertEqual([], Decision(decision).expectations())

        expectation1 = Frame("@TEST.EXPECTATION.?")
        expectation2 = Frame("@TEST.EXPECTATION.?")

        decision["HAS-EXPECTATION"] += expectation1
        decision["HAS-EXPECTATION"] += expectation2

        self.assertEqual([expectation1, expectation2], Decision(decision).expectations())

    def test_priority(self):
        decision = Frame("@TEST.DECISION")

        self.assertEqual(None, Decision(decision).priority())

        decision["HAS-PRIORITY"] = 0.5

        self.assertEqual(0.5, Decision(decision).priority())

    def test_cost(self):
        decision = Frame("@TEST.DECISION")

        self.assertEqual(None, Decision(decision).cost())

        decision["HAS-COST"] = 0.5

        self.assertEqual(0.5, Decision(decision).cost())

    def test_requires(self):
        decision = Frame("@TEST.DECISION")

        self.assertEqual([], Decision(decision).requires())

        capability1 = Frame("@TEST.CAPABILITY.?")
        capability2 = Frame("@TEST.CAPABILITY.?")

        output1 = Frame("@TEST.OUTPUT-XMR.?")
        output2 = Frame("@TEST.OUTPUT-XMR.?")

        output1["REQUIRES"] = capability1
        output2["REQUIRES"] = capability2

        decision["HAS-OUTPUT"] += output1
        decision["HAS-OUTPUT"] += output2

        self.assertEqual([capability1, capability2], Decision(decision).requires())

    def test_status(self):
        decision = Frame("@TEST.DECISION")

        self.assertEqual(Decision.Status.PENDING, Decision(decision).status())

        decision["STATUS"] = Decision.Status.SELECTED

        self.assertEqual(Decision.Status.SELECTED, Decision(decision).status())

    def test_effectors(self):
        decision = Frame("@TEST.DECISION")

        self.assertEqual([], Decision(decision).effectors())

        effector1 = Frame("@TEST.EFFECTOR.?")
        effector2 = Frame("@TEST.EFFECTOR.?")

        decision["HAS-EFFECTOR"] += effector1
        decision["HAS-EFFECTOR"] += effector2

        self.assertEqual([effector1, effector2], Decision(decision).effectors())

    def test_callbacks(self):
        decision = Frame("@TEST.DECISION")

        self.assertEqual([], Decision(decision).callbacks())

        callback1 = Frame("@TEST.CALLBACK.?")
        callback2 = Frame("@TEST.CALLBACK.?")

        decision["HAS-CALLBACK"] += callback1
        decision["HAS-CALLBACK"] += callback2

        self.assertEqual([callback1, callback2], Decision(decision).callbacks())

    def test_build(self):
        goal = Frame("@TEST.GOAL")
        plan = Frame("@TEST.PLAN")
        step = Frame("@TEST.STEP")

        decision = Decision.build(Space("TEST"), goal, plan, step)

        self.assertEqual(goal, decision.goal())
        self.assertEqual(plan, decision.plan())
        self.assertEqual(step, decision.step())
        self.assertEqual([], decision.outputs())
        self.assertEqual(None, decision.priority())
        self.assertEqual(None, decision.cost())
        self.assertEqual([], decision.requires())
        self.assertEqual(Decision.Status.PENDING, decision.status())
        self.assertEqual([], decision.callbacks())

    def test_generate_outputs_populates_outputs(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        agent = Frame("@TEST.AGENT")
        capability = Frame("@TEST.CAPABILITY")

        template = OutputXMRTemplate.build("test-template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(Space("TEST"), template, [], agent)
        goal = Goal(Frame("@TEST.GOAL"))
        step = Step.build(Space("TEST"), 1, statement)

        decision = Decision.build(Space("TEST"), goal, "TEST-PLAN", step)

        self.assertEqual([], decision.outputs())

        decision._generate_outputs()

        self.assertEqual([Frame("@OUTPUTS.XMR.1")], decision.outputs())

    def test_generate_outputs_populates_expectations(self):
        from backend.models.statement import ExpectationStatement, IsStatement

        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        target = Frame("@TEST.TARGET")

        statement = ExpectationStatement.instance(Space("TEST"), IsStatement.instance(Space("TEST"), target, "SLOT", 123))
        goal = Goal(Frame("@TEST.GOAL"))
        step = Step.build(Space("TEST"), 1, statement)

        decision = Decision.build(Space("TEST"), goal, "TEST-PLAN", step)

        self.assertEqual([], decision.expectations())

        decision._generate_outputs()

        self.assertEqual([Frame("@TEST.EXPECTATION.1")], decision.expectations())

    def test_generate_outputs_halts_and_registers_impasses(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import AssertStatement, ExistsStatement, MakeInstanceStatement, OutputXMRStatement, Variable

        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        Goal.define(Space("TEST"), "IMPASSE-GOAL", 0.5, 0.5, [], [], ["$var1"], [])

        resolution = MakeInstanceStatement.instance(Space("TEST"), "TEST", "@TEST.IMPASSE-GOAL", ["$var1"])
        statement1 = AssertStatement.instance(Space("TEST"), ExistsStatement.instance(Space("TEST"), Query(IdComparator("@EXE.DNE"))), [resolution])

        template = OutputXMRTemplate.build("test-template", XMR.Type.ACTION, None, [])
        statement2 = OutputXMRStatement.instance(Space("TEST"), template, [], None)

        goal = Goal(Frame("@TEST.GOAL"))
        Variable.instance(Space("TEST"), "$var1", 123, goal)
        step = Step.build(Space("TEST"), 1, [statement1, statement2])
        decision = Decision.build(Space("TEST"), goal, "TEST-PLAN", step)

        self.assertEqual([], decision.impasses())
        self.assertEqual([], decision.outputs())
        self.assertEqual([], goal.subgoals())

        decision._generate_outputs()

        self.assertEqual(1, len(decision.impasses()))
        self.assertEqual("IMPASSE-GOAL", decision.impasses()[0].name())
        self.assertEqual("@TEST.IMPASSE-GOAL.1", decision.impasses()[0].frame.id)
        self.assertEqual(123, decision.impasses()[0].resolve("$var1"))

        self.assertEqual("@TEST.IMPASSE-GOAL.1", goal.subgoals()[0].frame.id)

        self.assertEqual(Decision.Status.BLOCKED, decision.status())

        self.assertEqual([], decision.outputs())

    def test_calculate_priority(self):
        definition = Goal.define(Space("TEST"), "TEST-GOAL", 1.0, 0.0, [], [], [], [])
        goal = Goal.instance_of(Space("TEST"), definition, [])

        decision = Decision.build(Space("TEST"), goal, "TEST.PLAN", "TEST.STEP")

        self.assertIsNone(decision.priority())

        decision._calculate_priority()

        self.assertEqual(1.0, decision.priority())

    def test_calculate_cost(self):
        definition = Goal.define(Space("TEST"), "TEST-GOAL", 0.0, 1.0, [], [], [], [])
        goal = Goal.instance_of(Space("TEST"), definition, [])

        decision = Decision.build(Space("TEST"), goal, "TEST.PLAN", "TEST.STEP")

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
        decision = Decision.build(Space("TEST"), "TEST.GOAL", "TEST.PLAN", "TEST.STEP")
        self.assertEqual(Decision.Status.PENDING, decision.status())

        decision.select()
        self.assertEqual(Decision.Status.SELECTED, decision.status())

    def test_decline(self):
        decision = Decision.build(Space("TEST"), "TEST.GOAL", "TEST.PLAN", "TEST.STEP")
        self.assertEqual(Decision.Status.PENDING, decision.status())

        decision.decline()
        self.assertEqual(Decision.Status.DECLINED, decision.status())

    def test_execute(self):
        from backend.models.effectors import Capability, Effector
        from backend.models.mps import MPRegistry, OutputMethod

        out = False

        class TestMP(OutputMethod):
            def run(self):
                nonlocal out
                out = True

        MPRegistry.register(TestMP)
        capability = Capability.instance(Space("TEST"), "CAPABILITY", "TestMP", ["ONT.EVENT"])
        output = XMR.instance(Space("TEST"), "OUTPUT-XMR", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "@TEST.FRAME.1", "", capability=capability)

        decision = Decision.build(Space("TEST"), "GOAL", "PLAN", "STEP")
        decision.frame["HAS-OUTPUT"] += output.frame

        effector = Effector.instance(Space("TEST"), Effector.Type.PHYSICAL, [capability])
        effector.reserve(decision, output, capability)

        decision.execute(None, [effector])

        self.assertTrue(out)
        self.assertIn(effector, decision.effectors())
        self.assertEqual(Decision.Status.EXECUTING, decision.status())

    def test_creates_callback(self):
        from backend.models.effectors import Callback, Capability, Effector
        from backend.models.mps import MPRegistry, OutputMethod

        class TestMP(OutputMethod):
            def run(self): pass

        MPRegistry.register(TestMP)
        capability = Capability.instance(Space("TEST"), "CAPABILITY", "TestMP", ["ONT.EVENT"])
        output = XMR.instance(Space("TEST"), "OUTPUT-XMR", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "@TEST.FRAME.1", "", capability=capability)

        decision = Decision.build(Space("TEST"), "GOAL", "PLAN", "STEP")
        decision.frame["HAS-OUTPUT"] += output.frame

        effector = Effector.instance(Space("TEST"), Effector.Type.PHYSICAL, [capability])
        effector.reserve(decision, output, capability)

        decision.execute(None, [effector])

        callback = Frame("@TEST.CALLBACK.1")
        self.assertIn(callback, decision.callbacks())
        self.assertEqual(decision, Callback(callback).decision())
        self.assertEqual(effector, Callback(callback).effector())

    def test_callback_received(self):
        from backend.models.effectors import Callback, Capability, Effector
        from backend.models.mps import MPRegistry, OutputMethod

        class TestMP(OutputMethod):
            def run(self): pass

        MPRegistry.register(TestMP)
        capability = Capability.instance(Space("TEST"), "CAPABILITY", "TestMP", ["ONT.EVENT"])
        output = XMR.instance(Space("TEST"), "OUTPUT-XMR", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "@TEST.FRAME.1", "", capability=capability)

        decision = Decision.build(Space("TEST"), "GOAL", "PLAN", "STEP")
        decision.frame["HAS-OUTPUT"] += output.frame

        effector = Effector.instance(Space("TEST"), Effector.Type.PHYSICAL, [capability])
        effector.reserve(decision, output, capability)

        callback = Callback.build(Space("TEST"), decision, effector)

        decision.frame["HAS-EFFECTOR"] = effector.frame
        decision.frame["HAS-CALLBACK"] = callback.frame

        decision.callback_received(callback)
        self.assertNotIn(effector, decision.effectors())
        self.assertNotIn(callback, decision.callbacks())

    def test_assess_impasses(self):

        subgoal1 = Frame("@TEST.GOAL.?")
        subgoal1["STATUS"] = Goal.Status.ACTIVE

        subgoal2 = Frame("@TEST.GOAL.?")
        subgoal2["STATUS"] = Goal.Status.SATISFIED

        decision = Frame("@TEST.DECISION.?")
        decision["HAS-IMPASSE"] += subgoal1
        decision["HAS-IMPASSE"] += subgoal2

        self.assertEqual([subgoal1, subgoal2], Decision(decision).impasses())

        Decision(decision).assess_impasses()

        self.assertEqual([subgoal1], Decision(decision).impasses())


class ExpectationTestCase(unittest.TestCase):

    def setUp(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

    def test_status(self):
        e = Frame("@TEST.EXPECTATION")
        e["STATUS"] = Expectation.Status.EXPECTING

        self.assertEqual(Expectation.Status.EXPECTING, Expectation(e).status())

    def test_condition(self):
        from backend.models.statement import ExistsStatement

        e = Frame("@TEST.EXPECTATION")
        e["CONDITION"] = ExistsStatement.instance(Space("TEST"), Query(IdComparator("@TEST.FRAME.1"))).frame

        self.assertEqual(ExistsStatement.instance(Space("TEST"), Query(IdComparator("@TEST.FRAME.1"))), Expectation(e).condition())

    def test_build(self):
        from backend.models.statement import ExistsStatement

        e = Expectation.build(Space("TEST"), Expectation.Status.EXPECTING, ExistsStatement.instance(Space("TEST"), Query(IdComparator("@TEST.FRAME.1"))))

        self.assertEqual(Expectation.Status.EXPECTING, e.status())
        self.assertEqual(ExistsStatement.instance(Space("TEST"), Query(IdComparator("@TEST.FRAME.1"))), e.condition())

    def test_assess(self):
        from backend.models.statement import IsStatement

        target = Frame("@TEST.TARGET")
        varmap = VariableMap(Frame("@TEST.VARMAP"))

        e = Expectation.build(Space("TEST"), Expectation.Status.PENDING, IsStatement.instance(Space("TEST"), target, "SLOT", 123))
        self.assertEqual(Expectation.Status.PENDING, e.status())

        e.assess(varmap)
        self.assertEqual(Expectation.Status.PENDING, e.status())

        target["SLOT"] = 123
        e.assess(varmap)
        self.assertEqual(Expectation.Status.SATISFIED, e.status())

        target["SLOT"] = 456
        e.assess(varmap)
        self.assertEqual(Expectation.Status.PENDING, e.status())


class EffectTestCase(unittest.TestCase):

    def setUp(self):
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

    def test_statements(self):
        from backend.models.statement import AddFillerStatement

        statement1 = AddFillerStatement.instance(Space("TEST"), "TEST.FRAME.1", "SLOT", 123)
        statement2 = AddFillerStatement.instance(Space("TEST"), "TEST.FRAME.1", "SLOT", 123)

        frame = Frame("@TEST.EFFECT")
        frame["HAS-STATEMENT"] += statement1.frame
        frame["HAS-STATEMENT"] += statement2.frame

        self.assertEqual([statement1, statement2], Effect(frame).statements())

    def test_build(self):
        from backend.models.statement import AddFillerStatement

        statement1 = AddFillerStatement.instance(Space("TEST"), "TEST.FRAME.1", "SLOT", 123)
        statement2 = AddFillerStatement.instance(Space("TEST"), "TEST.FRAME.1", "SLOT", 123)

        effect = Effect.build(Space("TEST"), [statement1, statement2])

        self.assertEqual([statement1, statement2], effect.statements())

    def test_apply(self):
        from backend.models.statement import AddFillerStatement, Variable

        statement1 = AddFillerStatement.instance(Space("TEST"), "@TEST.FRAME.1", "SLOT", 123)
        statement2 = AddFillerStatement.instance(Space("TEST"), "@TEST.FRAME.1", "SLOT", "$var1")

        effect = Effect.build(Space("TEST"), [statement1, statement2])

        frame = Frame("@TEST.FRAME.?")

        self.assertEqual([], frame["SLOT"])

        varmap = VariableMap(Frame("@TEST.VARMAP"))
        Variable.instance(Space("TEST"), "$var1", 456, varmap)
        effect.apply(varmap)

        self.assertEqual([123, 456], frame["SLOT"])