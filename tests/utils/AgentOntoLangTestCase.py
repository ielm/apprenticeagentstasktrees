from backend import agent
from backend.models.agenda import Agenda, Condition, Effect, Goal, Plan, Step
from backend.models.mps import AgentMethod, MPRegistry
from backend.models.output import OutputXMRTemplate
from backend.models.statement import AddFillerStatement, AssertStatement, AssignFillerStatement, AssignVariableStatement, ExistsStatement, ExpectationStatement, ForEachStatement, IsStatement, MakeInstanceStatement, MeaningProcedureStatement, OutputXMRStatement, TransientFrameStatement
from backend.models.xmr import XMR
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.OntoLang import AssignOntoLangProcessor
from ontograph.Query import ExistsComparator, IdComparator, Query
from ontograph.Space import Space
from utils.AgentOntoLang import AgentOntoLang, OntoAgentProcessorAddGoalInstance, OntoAgentProcessorAddTrigger, OntoAgentProcessorDefineOutputXMRTemplate, OntoAgentProcessorRegisterMP
import unittest


class AgentOntoLangTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        self.ontolang = AgentOntoLang()

    def test_add_trigger(self):
        query = Query(ExistsComparator(slot="THEME", filler=123, isa=False))

        processor = OntoAgentProcessorAddTrigger("@SELF.AGENDA.1", "@EXE.MYGOAL.1", query)
        parsed = self.ontolang.parse("ADD TRIGGER TO @SELF.AGENDA.1 INSTANTIATE @EXE.MYGOAL.1 WHEN THEME = 123;")

        self.assertEqual([processor], parsed)

    def test_plan(self):
        self.ontolang.get_starting_rule = lambda: "plan"

        stmt = Frame("@EXE.EXISTS-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = ExistsStatement.__qualname__

        stmt = Frame("@EXE.MP-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = MeaningProcedureStatement.__qualname__

        space = Space("SELF")

        plan = Plan.build(space, "testplan", Plan.DEFAULT, Step.build(space, 1, Step.IDLE))
        parsed = self.ontolang.parse("PLAN (testplan) SELECT DEFAULT STEP DO IDLE")
        self.assertEqual(plan, parsed)

        query = Query(ExistsComparator(slot="THEME", filler=123, isa=False))
        plan = Plan.build(space, "testplan", ExistsStatement.instance(space, query), Step.build(space, 1, Step.IDLE))
        parsed = self.ontolang.parse("PLAN (testplan) SELECT IF EXISTS THEME = 123 STEP DO IDLE")
        self.assertEqual(plan, parsed)

        statement = MeaningProcedureStatement.instance(space, "mp1", ["$var1"])
        plan = Plan.build(space, "testplan", statement, Step.build(space, 1, Step.IDLE))
        parsed = self.ontolang.parse( "PLAN (testplan) SELECT IF SELF.mp1($var1) STEP DO IDLE")
        self.assertEqual(plan, parsed)

        statement = MeaningProcedureStatement.instance(space, "mp1", ["$var1"])
        plan = Plan.build(space, "testplan", statement, Step.build(space, 1, Step.IDLE), negate=True)
        parsed = self.ontolang.parse("PLAN (testplan) SELECT IF NOT SELF.mp1($var1) STEP DO IDLE")
        self.assertEqual(plan, parsed)

        statement = MeaningProcedureStatement.instance(space, "mp1", [])
        plan = Plan.build(space, "testplan", Plan.DEFAULT, Step.build(space, 1, [statement, statement]))
        parsed = self.ontolang.parse("PLAN (testplan) SELECT DEFAULT STEP DO SELF.mp1() DO SELF.mp1()")
        self.assertEqual(plan, parsed)

        statement = MeaningProcedureStatement.instance(space, "mp1", [])
        plan = Plan.build(space, "testplan", Plan.DEFAULT, [Step.build(space, 1, [statement]), Step.build(space, 2, [statement])])
        parsed = self.ontolang.parse("PLAN (testplan) SELECT DEFAULT STEP DO SELF.mp1() STEP DO SELF.mp1()")
        self.assertEqual(plan, parsed)

    def test_condition(self):
        self.ontolang.get_starting_rule = lambda: "condition"

        stmt = Frame("@EXE.EXISTS-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = ExistsStatement.__qualname__

        space = Space("SELF")

        query = Query(ExistsComparator(slot="THEME", filler=123, isa=False))

        condition = Condition.build(space, [ExistsStatement.instance(space, query)], Goal.Status.SATISFIED, logic=Condition.Logic.AND, order=1)
        parsed = self.ontolang.parse("WHEN EXISTS THEME = 123 THEN satisfied")
        self.assertEqual(condition, parsed)

        condition = Condition.build(space, [ExistsStatement.instance(space, query), ExistsStatement.instance(space, query)], Goal.Status.SATISFIED, logic=Condition.Logic.AND, order=1)
        parsed = self.ontolang.parse("WHEN EXISTS THEME = 123 AND EXISTS THEME = 123 THEN satisfied")
        self.assertEqual(condition, parsed)

        condition = Condition.build(space, [ExistsStatement.instance(space, query), ExistsStatement.instance(space, query)], Goal.Status.SATISFIED, logic=Condition.Logic.OR, order=1)
        parsed = self.ontolang.parse("WHEN EXISTS THEME = 123 OR EXISTS THEME = 123 THEN satisfied")
        self.assertEqual(condition, parsed)

        condition = Condition.build(space, [], Goal.Status.SATISFIED, on=Condition.On.EXECUTED)
        parsed = self.ontolang.parse("WHEN EXECUTED THEN satisfied")
        self.assertEqual(condition, parsed)

    def test_define_goal(self):
        space = Space("TEST")
        exists = Frame("@EXE.EXISTS-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        exists["CLASSMAP"] = ExistsStatement.__qualname__

        # A goal has a name and a destination graph, and a default priority
        goal: Goal = self.ontolang.parse("DEFINE XYZ() AS GOAL IN SELF;")[0].goal
        self.assertTrue(goal.frame in Space("SELF"))
        self.assertEqual(goal.name(), "XYZ")
        self.assertEqual(goal.priority(), 0.5)

        # A goal can be overwritten
        goal: Goal = self.ontolang.parse("DEFINE XYZ() AS GOAL IN SELF;")[0].goal
        self.assertTrue(goal.frame in Space("SELF"))
        self.assertEqual(goal.name(), "XYZ")
        self.assertEqual(1, len(Space("SELF"))) # One is the agent, the other is the overwritten goal

        # A goal can have parameters
        goal: Goal = Goal.define(space, "XYZ", 0.5, 0.5, [], [], ["$var1", "$var2"], [])
        parsed: Goal = self.ontolang.parse("DEFINE XYZ($var1, $var2) AS GOAL IN SELF;")[0].goal
        self.assertEqual(goal, parsed)

        # A goal can have a numeric priority
        goal: Goal = Goal.define(space, "XYZ", 0.9, 0.5, [], [], [], [])
        parsed: Goal = self.ontolang.parse("DEFINE XYZ() AS GOAL IN SELF PRIORITY 0.9;")[0].goal
        self.assertEqual(goal, parsed)

        # A goal can have a statement priority
        goal: Goal = Goal.define(space, "XYZ", MeaningProcedureStatement.instance(space, "mp1", []).frame, 0.5, [], [], [], [])
        parsed: Goal = self.ontolang.parse("DEFINE XYZ() AS GOAL IN SELF PRIORITY SELF.mp1();")[0].goal
        self.assertEqual(goal.frame["PRIORITY"].singleton()["CALLS"].singleton(), parsed.frame["PRIORITY"].singleton()["CALLS"].singleton())

        # A goal can have a numeric resources
        goal: Goal = Goal.define(space, "XYZ", 0.5, 0.9, [], [], [], [])
        parsed: Goal = self.ontolang.parse("DEFINE XYZ() AS GOAL IN SELF RESOURCES 0.9;")[0].goal
        self.assertEqual(goal, parsed)

        # A goal can have a statement resources
        goal: Goal = Goal.define(space, "XYZ", 0.5, MeaningProcedureStatement.instance(space, "mp1", []).frame, [], [], [], [])
        parsed: Goal = self.ontolang.parse("DEFINE XYZ() AS GOAL IN SELF RESOURCES SELF.mp1();")[0].goal
        self.assertEqual(goal.frame["RESOURCES"].singleton()["CALLS"].singleton(), parsed.frame["RESOURCES"].singleton()["CALLS"].singleton())

        # A goal can have plans (plans)
        a1: Plan = Plan.build(space, "plan_a", Plan.DEFAULT, Step.build(space, 1, Step.IDLE))
        a2: Plan = Plan.build(space, "plan_b", Plan.DEFAULT, Step.build(space, 1, Step.IDLE))
        goal: Goal = Goal.define(space, "XYZ", 0.5, 0.5, [a1, a2], [], [], [])
        parsed: Goal = self.ontolang.parse("DEFINE XYZ() AS GOAL IN SELF PLAN (plan_a) SELECT DEFAULT STEP DO IDLE PLAN (plan_b) SELECT DEFAULT STEP DO IDLE;")[0].goal
        self.assertEqual(goal, parsed)

        # A goal can have conditions (which are ordered as written)
        q1 = Query(ExistsComparator(slot="THEME", filler=123, isa=False))
        q2 = Query(ExistsComparator(slot="THEME", filler=456, isa=False))
        c1: Condition = Condition.build(space, [ExistsStatement.instance(space, q1)], Goal.Status.SATISFIED, Condition.Logic.AND, 1)
        c2: Condition = Condition.build(space, [ExistsStatement.instance(space, q2)], Goal.Status.ABANDONED, Condition.Logic.AND, 2)
        goal: Goal = Goal.define(space, "XYZ", 0.5, 0.5, [], [c1, c2], [], [])
        parsed: Goal = self.ontolang.parse("DEFINE XYZ() AS GOAL IN SELF WHEN EXISTS THEME = 123 THEN satisfied WHEN EXISTS THEME = 456 THEN abandoned;")[0].goal
        self.assertEqual(goal, parsed)

        # A goal can have effects
        e1: Effect = Effect.build(space, [AddFillerStatement.instance(space, "@TEST.FRAME.1", "SLOT", 123)])
        e2: Effect = Effect.build(space, [AddFillerStatement.instance(space, "@TEST.FRAME.1", "SLOT", 456)])
        goal: Goal = Goal.define(space, "XYZ", 0.5, 0.5, [], [], [], [e1, e2])
        parsed: Goal = self.ontolang.parse("DEFINE XYZ() AS GOAL IN SELF EFFECT DO @TEST.FRAME.1[SLOT] += 123 DO @TEST.FRAME.1[SLOT] += $var1;")[0].goal
        self.assertEqual(goal, parsed)

    def test_register_mp(self):
        processor = OntoAgentProcessorRegisterMP(TestAgentMethod)
        parsed = self.ontolang.parse("REGISTER MP tests.utils.AgentOntoLangTestCase.TestAgentMethod;")
        self.assertEqual([processor], parsed)

        processor = OntoAgentProcessorRegisterMP(TestAgentMethod, name="TestMP")
        parsed = self.ontolang.parse("REGISTER MP tests.utils.AgentOntoLangTestCase.TestAgentMethod AS TestMP;")
        self.assertEqual([processor], parsed)

    def test_add_goal_instance(self):
        processor = OntoAgentProcessorAddGoalInstance(Frame("@TEST.GOAL"), [])
        parsed = self.ontolang.parse("ADD GOAL INSTANCE @TEST.GOAL();")
        self.assertEqual([processor], parsed)

        processor = OntoAgentProcessorAddGoalInstance(Frame("@TEST.GOAL"), [123])
        parsed = self.ontolang.parse("ADD GOAL INSTANCE @TEST.GOAL(123);")
        self.assertEqual([processor], parsed)

        processor = OntoAgentProcessorAddGoalInstance(Frame("@TEST.GOAL"), [123, "hi", Frame("@TEST.FRAME.1")])
        parsed = self.ontolang.parse("ADD GOAL INSTANCE @TEST.GOAL(123, \"hi\", @TEST.FRAME.1);")
        self.assertEqual([processor], parsed)

    def test_find_something_to_do(self):
        from ontograph.Query import AndComparator, IsAComparator

        self.ontolang.get_starting_rule = lambda: "ontoagent_process_define_goal"

        stmt = Frame("@EXE.EXISTS-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = ExistsStatement.__qualname__

        space = Space("SELF")

        query = Query(AndComparator([IsAComparator("@SELF.INPUT-TMR"), ExistsComparator(slot="ACKNOWLEDGED", filler=False, isa=False)]))

        goal1 = Goal.define(space, "FIND-SOMETHING-TO-DO", 0.1, 0.5, [
            Plan.build(space,
                         "acknowledge input",
                         ExistsStatement.instance(space, query),
                         Step.build(space, 1,
                                    ForEachStatement.instance(
                                        space,
                                        query,
                                        "$tmr",
                                        [
                                            AddFillerStatement.instance(space, "@SELF.ROBOT.1", "HAS-GOAL", MakeInstanceStatement.instance(space, "SELF", "@SELF.UNDERSTAND-TMR", ["$tmr"])),
                                           AssignFillerStatement.instance(space, "$tmr", "ACKNOWLEDGED", True)
                                        ])
                         )),
            Plan.build(space, "idle", Plan.DEFAULT, [Step.build(space, 1, Step.IDLE), Step.build(space, 2, Step.IDLE)])
        ], [], [], [])

        script = '''
        DEFINE FIND-SOMETHING-TO-DO()
            AS GOAL
            IN SELF
            PRIORITY 0.1
            PLAN (acknowledge input)
                SELECT IF EXISTS (@ ISA @SELF.INPUT-TMR AND ACKNOWLEDGED = FALSE)
                STEP
                    DO FOR EACH $tmr IN (@ ISA @SELF.INPUT-TMR AND ACKNOWLEDGED = FALSE)
                    | SELF[HAS-GOAL] += @SELF:@SELF.UNDERSTAND-TMR($tmr)
                    | $tmr[ACKNOWLEDGED] = True
            PLAN (idle)
                SELECT DEFAULT
                STEP
                    DO IDLE
                STEP
                    DO IDLE
        ;
        '''

        parsed: Goal = self.ontolang.parse(script).goal
        self.assertEqual(goal1, parsed)


class AgentOntoLangStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        self.ontolang = AgentOntoLang()

    def test_statement_instance(self):
        self.ontolang.get_starting_rule = lambda: "statement_instance"

        space = Space("SELF")
        concept = Frame("@SELF.MYCONCEPT")
        instance = Frame("@SELF.FRAME.?")

        # SELF refers to the agent's identity
        self.assertEqual("@SELF.ROBOT.1", self.ontolang.parse("SELF"))

        # An instance can be created on a specified graph (by name); here "SELF" is the graph name, and SELF.MYCONCEPT is an identifier to make an instance of
        self.assertEqual(MakeInstanceStatement.instance(space, "SELF", concept, []), self.ontolang.parse("@SELF:@SELF.MYCONCEPT()"))

        # New instances can include arguments
        self.assertEqual(MakeInstanceStatement.instance(space, "SELF", concept, ["$arg1", "$arg2"]), self.ontolang.parse("@SELF:@SELF.MYCONCEPT($arg1, $arg2)"))

        # A simple identifier is also a valid statement instance
        self.assertEqual(instance, self.ontolang.parse("@SELF.FRAME.1"))

        # Any variable can also be used
        self.assertEqual("$var1", self.ontolang.parse("$var1"))

    def test_is_statement(self):
        self.ontolang.get_starting_rule = lambda : "is_statement"

        f = Frame("@SELF.FRAME")

        self.assertEqual(IsStatement.instance(Space("SELF"), f, "SLOT", 123), self.ontolang.parse("@SELF.FRAME[SLOT] == 123"))

    def test_make_instance_statement(self):
        self.ontolang.get_starting_rule = lambda: "make_instance_statement"

        space = Space("SELF")
        concept = Frame("@SELF.MYCONCEPT")
        self.assertEqual(MakeInstanceStatement.instance(space, space.name, concept, []), self.ontolang.parse("@SELF:@SELF.MYCONCEPT()"))
        self.assertEqual(MakeInstanceStatement.instance(space, space.name, concept, ["$arg1", "$arg2"]), self.ontolang.parse("@SELF:@SELF.MYCONCEPT($arg1, $arg2)"))

    def test_add_filler_statement(self):
        self.ontolang.get_starting_rule = lambda: "add_filler_statement"

        space = Space("SELF")
        f = Frame("@SELF.FRAME")

        statement = AddFillerStatement.instance(space, "@SELF.ROBOT.1", "SLOT", 123)
        parsed = self.ontolang.parse("SELF[SLOT] += 123")
        self.assertEqual(statement, parsed)

        statement = AddFillerStatement.instance(space, "@SELF.ROBOT.1", "SLOT", f)
        parsed = self.ontolang.parse("SELF[SLOT] += @SELF.FRAME")
        self.assertEqual(statement, parsed)

        statement = AddFillerStatement.instance(space, f, "SLOT", 123)
        parsed = self.ontolang.parse("@SELF.FRAME[SLOT] += 123")
        self.assertEqual(statement, parsed)

    def test_assert_statement(self):
        self.ontolang.get_starting_rule = lambda: "assert_statement"

        stmt = Frame("@EXE.EXISTS-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = ExistsStatement.__qualname__

        stmt = Frame("@EXE.IS-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = IsStatement.__qualname__

        stmt = Frame("@EXE.MP-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = MeaningProcedureStatement.__qualname__

        space = Space("SELF")
        f = Frame("@SELF.FRAME")

        resolution1 = MakeInstanceStatement.instance(space, "TEST", "@TEST.MYGOAL", [])
        resolution2 = MakeInstanceStatement.instance(space, "TEST", "@TEST.MYGOAL", ["$var1", "$var2"])

        statement = AssertStatement.instance(space, ExistsStatement.instance(space, Query(ExistsComparator(slot="XYZ", isa=False))), [resolution1])
        parsed = self.ontolang.parse("ASSERT EXISTS XYZ = * ELSE IMPASSE WITH @TEST:@TEST.MYGOAL()")
        self.assertEqual(statement, parsed)

        statement = AssertStatement.instance(space, IsStatement.instance(space, f, "SLOT", 123), [resolution1])
        parsed = self.ontolang.parse("ASSERT @SELF.FRAME[SLOT] == 123 ELSE IMPASSE WITH @TEST:@TEST.MYGOAL()")
        self.assertEqual(statement, parsed)

        statement = AssertStatement.instance(space, MeaningProcedureStatement.instance(space, "some_mp", ["$var1"]), [resolution1])
        parsed = self.ontolang.parse("ASSERT SELF.some_mp($var1) ELSE IMPASSE WITH @TEST:@TEST.MYGOAL()")
        self.assertEqual(statement, parsed)

        statement = AssertStatement.instance(space, ExistsStatement.instance(space, Query(ExistsComparator(slot="XYZ", isa=False))), [resolution1, resolution2])
        parsed = self.ontolang.parse("ASSERT EXISTS XYZ = * ELSE IMPASSE WITH @TEST:@TEST.MYGOAL() OR @TEST:@TEST.MYGOAL($var1, $var2)")
        self.assertEqual(statement, parsed)

    def test_assign_filler_statement(self):
        self.ontolang.get_starting_rule = lambda: "assign_filler_statement"

        space = Space("SELF")
        f = Frame("@SELF.FRAME")

        statement = AssignFillerStatement.instance(space, "@SELF.ROBOT.1", "SLOT", 123)
        parsed = self.ontolang.parse("SELF[SLOT] = 123")
        self.assertEqual(statement, parsed)

        statement = AssignFillerStatement.instance(space, "@SELF.ROBOT.1", "SLOT", f)
        parsed = self.ontolang.parse("SELF[SLOT] = @SELF.FRAME")
        self.assertEqual(statement, parsed)

        statement = AssignFillerStatement.instance(space, f, "SLOT", 123)
        parsed = self.ontolang.parse("@SELF.FRAME[SLOT] = 123")
        self.assertEqual(statement, parsed)

    def test_assign_variable_statement(self):
        self.ontolang.get_starting_rule = lambda: "assign_variable_statement"

        from backend.models.statement import TransientTriple

        space = Space("SELF")
        f = Frame("@SELF.FRAME")

        statement = AssignVariableStatement.instance(space, "$var1", 123)
        parsed = self.ontolang.parse("$var1 = 123")
        self.assertEqual(statement, parsed)

        statement = AssignVariableStatement.instance(space, "$var1", "test")
        parsed = self.ontolang.parse("$var1 = \"test\"")
        self.assertEqual(statement, parsed)

        statement = AssignVariableStatement.instance(space, "$var1", f)
        parsed = self.ontolang.parse("$var1 = @SELF.FRAME")
        self.assertEqual(statement, parsed)

        statement = AssignVariableStatement.instance(space, "$var1", "$var2")
        parsed = self.ontolang.parse("$var1 = $var2")
        self.assertEqual(statement, parsed)

        statement = AssignVariableStatement.instance(space, "$var1", MeaningProcedureStatement.instance(space, "TestMP", []))
        parsed = self.ontolang.parse("$var1 = SELF.TestMP()")
        self.assertEqual(statement, parsed)

        statement = AssignVariableStatement.instance(space, "$var1", ExistsStatement.instance(space, Query(IdComparator("@EXE.TEST.1"))))
        parsed = self.ontolang.parse("$var1 = EXISTS @ = @EXE.TEST.1")
        self.assertEqual(statement, parsed)

        statement = AssignVariableStatement.instance(space, "$var1", [[123, "test", "$var2", MeaningProcedureStatement.instance(space, "TestMP", [])]])
        parsed = self.ontolang.parse("$var1 = [123, \"test\", $var2, SELF.TestMP()]")
        self.assertIsInstance(parsed.frame["ASSIGN"][0], list)
        self.assertEqual(statement, parsed)

        statement = AssignVariableStatement.instance(space, "$var1", [[]])
        parsed = self.ontolang.parse("$var1 = []")
        self.assertIsInstance(parsed.frame["ASSIGN"][0], list)
        self.assertEqual(statement, parsed)

        statement = AssignVariableStatement.instance(space, "$var1", TransientFrameStatement.instance(space, [TransientTriple("SLOT", 123)]))
        parsed = self.ontolang.parse("$var1 = {SLOT 123;}")
        self.assertEqual(statement, parsed)

    def test_exists_statement(self):
        self.ontolang.get_starting_rule = lambda: "exists_statement"

        statement = ExistsStatement.instance(Space("SELF"), Query(ExistsComparator(slot="THEME", filler=123, isa=False)))
        parsed = self.ontolang.parse("EXISTS THEME = 123")
        self.assertEqual(statement, parsed)

    def test_expectation_statement(self):
        self.ontolang.get_starting_rule = lambda: "expectation_statement"

        stmt = Frame("@EXE.EXISTS-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = ExistsStatement.__qualname__

        stmt = Frame("@EXE.IS-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = IsStatement.__qualname__

        stmt = Frame("@EXE.MP-STATEMENT").add_parent("@EXE.BOOLEAN-STATEMENT")
        stmt["CLASSMAP"] = MeaningProcedureStatement.__qualname__

        space = Space("SELF")

        statement = ExpectationStatement.instance(space, ExistsStatement.instance(space, Query(ExistsComparator(slot="XYZ", isa=False))))
        parsed = self.ontolang.parse("EXPECT EXISTS XYZ = *")
        self.assertEqual(statement, parsed)

        statement = ExpectationStatement.instance(space, MeaningProcedureStatement.instance(space, "test_mp", ["$var1"]))
        parsed = self.ontolang.parse("EXPECT SELF.test_mp($var1)")
        self.assertEqual(statement, parsed)

        statement = ExpectationStatement.instance(space, IsStatement.instance(space, Identifier("@SELF.FRAME.1"), "SLOT", 123))
        parsed = self.ontolang.parse("EXPECT @SELF.FRAME.1[SLOT] == 123")
        self.assertEqual(statement, parsed)

    def test_foreach_statement(self):
        self.ontolang.get_starting_rule = lambda: "foreach_statement"

        stmt = Frame("@EXE.ADDFILLER-STATEMENT").add_parent("@EXE.STATEMENT")
        stmt["CLASSMAP"] = AddFillerStatement.__qualname__

        space = Space("SELF")

        query = Query(ExistsComparator(slot="THEME", filler=123, isa=False))

        statement = ForEachStatement.instance(space, query, "$var", AddFillerStatement.instance(space, "$var", "SLOT", 456))
        parsed = self.ontolang.parse("FOR EACH $var IN THEME = 123 | $var[SLOT] += 456")
        self.assertEqual(statement, parsed)

        statement = ForEachStatement.instance(space, query, "$var", [AddFillerStatement.instance(space, "$var", "SLOT", 456), AddFillerStatement.instance(space, "$var", "SLOT", 456)])
        parsed = self.ontolang.parse("FOR EACH $var IN THEME = 123 | $var[SLOT] += 456 | $var[SLOT] += 456")
        self.assertEqual(statement, parsed)

    def test_mp_statement(self):
        self.ontolang.get_starting_rule = lambda: "mp_statement"

        space = Space("SELF")

        statement = MeaningProcedureStatement.instance(space, "mp1", [])
        parsed = self.ontolang.parse("SELF.mp1()")
        self.assertEqual(statement, parsed)

        statement = MeaningProcedureStatement.instance(space, "mp1", ["$var1", "$var2"])
        parsed = self.ontolang.parse("SELF.mp1($var1, $var2)")
        self.assertEqual(statement, parsed)

        statement = MeaningProcedureStatement.instance(space, "mp1", [123, Identifier("@SELF.TEST")])
        parsed = self.ontolang.parse("SELF.mp1(123, @SELF.TEST)")
        self.assertEqual(statement, parsed)

    def test_output_statement(self):
        self.ontolang.get_starting_rule = lambda: "output_statement"

        template = OutputXMRTemplate.build("test-xmr", XMR.Type.ACTION, "@SELF.TEST-CAPABILITY", ["$var1", "$var2", "$var3", "$var4"])

        statement = OutputXMRStatement.instance(Space("EXE"), template, [1, "abc", "$var1", Identifier("@SELF.TEST")], "@SELF.ROBOT.1")
        parsed = self.ontolang.parse("OUTPUT test-xmr(1, \"abc\", $var1, @SELF.TEST) BY SELF")
        self.assertEqual(statement, parsed)

    def test_transientframe_statement(self):
        self.ontolang.get_starting_rule = lambda: "transient_statement"

        from backend.models.statement import TransientTriple

        property1 = TransientTriple("SLOTA", 123)
        property2 = TransientTriple("SLOTA", 456)
        property3 = TransientTriple("SLOTB", "abc")
        property4 = TransientTriple("SLOTC", "$var1")
        property5 = TransientTriple("SLOTD", Identifier("@TEST.FRAME.1"))

        statement = TransientFrameStatement.instance(Space("EXE"), [property1])
        parsed = self.ontolang.parse("{SLOTA 123;}")
        self.assertEqual(statement, parsed)

        statement = TransientFrameStatement.instance(Space("EXE"), [property1, property2])
        parsed = self.ontolang.parse("{SLOTA 123; SLOTA 456;}")
        self.assertEqual(statement, parsed)

        statement = TransientFrameStatement.instance(Space("EXE"), [property3, property4, property5])
        parsed = self.ontolang.parse("{SLOTB \"abc\"; SLOTC $var1; SLOTD @TEST.FRAME.1;}")
        self.assertEqual(statement, parsed)


class AgentOntoLangDefineOutputXMRTemplateTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        self.ontolang = AgentOntoLang()

    def test_parse_type(self):
        self.ontolang.get_starting_rule = lambda: "output_xmr_template_type"

        type = XMR.Type.ACTION
        parsed = self.ontolang.parse("TYPE PHYSICAL")
        self.assertEqual(type, parsed)

        type = XMR.Type.MENTAL
        parsed = self.ontolang.parse("TYPE MENTAL")
        self.assertEqual(type, parsed)

        type = XMR.Type.LANGUAGE
        parsed = self.ontolang.parse("TYPE VERBAL")
        self.assertEqual(type, parsed)

    def test_parse_requires(self):
        self.ontolang.get_starting_rule = lambda: "output_xmr_template_requires"

        requires = Identifier("@EXE.TEST-CAPABILITY")
        parsed = self.ontolang.parse("REQUIRES @EXE.TEST-CAPABILITY")
        self.assertEqual(requires, parsed)

        requires = Identifier("@EXE.TEST-CAPABILITY.1")
        parsed = self.ontolang.parse("REQUIRES @EXE.TEST-CAPABILITY.1")
        self.assertEqual(requires, parsed)

    def test_parse_root(self):
        self.ontolang.get_starting_rule = lambda: "output_xmr_template_root"

        requires = Identifier("@OUT.TEST-ROOT")
        parsed = self.ontolang.parse("ROOT @OUT.TEST-ROOT")
        self.assertEqual(requires, parsed)

        requires = Identifier("@OUT.TEST-ROOT.1")
        parsed = self.ontolang.parse("ROOT @OUT.TEST-ROOT.1")
        self.assertEqual(requires, parsed)

    def test_parse_include(self):
        self.ontolang.get_starting_rule = lambda: "output_xmr_template_include"

        assign = AssignOntoLangProcessor("@OUT.MYFRAME.1")
        assign.append("MYPROP", Identifier("@ONT.ALL"))
        assign.append("OTHERPROP", "$var1")

        include = [assign]
        parsed = self.ontolang.parse("INCLUDE @OUT.MYFRAME.1 = {MYPROP @ONT.ALL; OTHERPROP \"$var1\";};")
        self.assertEqual(include, parsed)

        include = [AssignOntoLangProcessor("@OUT.MYFRAME.1"), AssignOntoLangProcessor("@OUT.MYFRAME.2")]
        parsed = self.ontolang.parse("INCLUDE @OUT.MYFRAME.1 = {}; @OUT.MYFRAME.2 = {};")
        self.assertEqual(include, parsed)

        assign = AssignOntoLangProcessor("@OUT.MYFRAME.1")
        assign.append("AGENT", "@SELF.ROBOT.1")

    def test_parse_template(self):
        self.ontolang.get_starting_rule = lambda: "ontoagent_process_define_output_xmr_template"

        input = '''
        DEFINE get-item-template($var1, $var2) AS TEMPLATE
            TYPE PHYSICAL
            REQUIRES @EXE.GET-CAPABILITY
            ROOT @OUT.POSSESSION-EVENT.1

            INCLUDE

            @OUT.POSSESSION-EVENT.1 = {
                AGENT  @SELF.ROBOT.1;
                THEME  "$var1";
                OTHER  @OUT.OBJECT.1;
            };

            @OUT.OBJECT.1 = {};
        ;
        '''

        name = "get-item-template"
        type = XMR.Type.ACTION
        capability = "@EXE.GET-CAPABILITY"
        params = ["$var1", "$var2"]
        root = "@OUT.POSSESSION-EVENT.1"

        assign1 = AssignOntoLangProcessor("@OUT.POSSESSION-EVENT.1")
        assign1.append("AGENT", Identifier("@SELF.ROBOT.1"))
        assign1.append("THEME", "$var1")
        assign1.append("OTHER", Identifier("@OUT.OBJECT.1"))

        assign2 = AssignOntoLangProcessor("@OUT.OBJECT.1")

        frames = [
            assign1,
            assign2
        ]

        bootstrap = OntoAgentProcessorDefineOutputXMRTemplate(name, type, capability, params, root, frames)
        parsed = self.ontolang.parse(input)
        self.assertEqual(bootstrap, parsed)


class OntoAgentProcessorAddTriggerTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_call(self):
        agenda = Frame("@TEST.AGENDA")
        definition = Frame("@TEST.DEFINITION")
        query = Query(IdComparator("@TEST.SOMETHING.123"))

        process = OntoAgentProcessorAddTrigger(agenda, definition, query)
        process.run()

        self.assertEqual(1, len(Agenda(agenda).triggers()))
        self.assertEqual(definition, Agenda(agenda).triggers()[0].definition())
        self.assertEqual(query, Agenda(agenda).triggers()[0].query())


class OntoAgentProcessorDefineOutputXMRTemplateTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        self.capability = Frame("@TEST.CAPABILITY")

    def test_call(self):
        name = "Test Name"
        type = XMR.Type.ACTION
        capability = self.capability
        params = ["$var1", "$var2"]
        root = "@OUT.EVENT.1"

        assign1 = AssignOntoLangProcessor("@OUT.EVENT.1")
        assign1.append("THEME", Identifier("@OUT.OBJECT.1"))

        assign2 = AssignOntoLangProcessor("@OUT.OBJECT.1")
        assign2.append("PROP", "$var1")

        frames = [assign1, assign2]

        process = OntoAgentProcessorDefineOutputXMRTemplate(name, type, capability, params, root, frames)
        process.run()

        template = Space("XMR-TEMPLATE#1")
        event = Frame("@XMR-TEMPLATE#1.EVENT.1")
        object = Frame("@XMR-TEMPLATE#1.OBJECT.1")

        self.assertEqual(object, event["THEME"])
        self.assertEqual("$var1", object["PROP"])

        self.assertEqual("Test Name", OutputXMRTemplate(template).name())
        self.assertEqual(XMR.Type.ACTION, OutputXMRTemplate(template).type())
        self.assertEqual(Frame("@TEST.CAPABILITY"), OutputXMRTemplate(template).capability().frame)
        self.assertEqual(["$var1", "$var2"], OutputXMRTemplate(template).params())


class OntoAgentProcessorRegisterMPTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        MPRegistry.clear()

        class MP(AgentMethod):
            def run(self):
                return True

        self.mp = MP

    def test_call(self):
        process = OntoAgentProcessorRegisterMP(self.mp)
        process.run()

        self.assertTrue(MPRegistry.has_mp(self.mp.__name__))
        self.assertTrue(MPRegistry.run(self.mp.__name__, None))

    def test_call_with_name(self):
        process = OntoAgentProcessorRegisterMP(self.mp, name="TestMP")
        process.run()

        self.assertTrue(MPRegistry.has_mp("TestMP"))
        self.assertTrue(MPRegistry.run("TestMP", None))


class OntoAgentProcessorAddGoalInstanceTestCase(unittest.TestCase):

    def setUp(self):
        agent.reset()

    def test_call(self):
        Goal.define(Space("TEST"), "GOAL", 0.5, 0.5, [], [], [], [])

        process = OntoAgentProcessorAddGoalInstance(Frame("@TEST.GOAL"), [])
        process.run()

        goals = agent.agenda().goals(pending=True)
        self.assertEqual(1, len(goals))
        self.assertTrue(goals[0].frame ^ Frame("@TEST.GOAL"))

    def test_call_with_params(self):
        Goal.define(Space("TEST"), "GOAL", 0.5, 0.5, [], [], ["$var1", "$var2", "$var3"], [])

        process = OntoAgentProcessorAddGoalInstance(Frame("@TEST.GOAL"), [123, "hi", Frame("@TEST.FRAME.1")])
        process.run()

        goals = agent.agenda().goals(pending=True)
        self.assertEqual(1, len(goals))
        goal = goals[0]

        self.assertEqual(123, goal.resolve("$var1"))
        self.assertEqual("hi", goal.resolve("$var2"))
        self.assertEqual(Frame("@TEST.FRAME.1"), goal.resolve("$var3"))


class TestAgentMethod(AgentMethod):
    pass