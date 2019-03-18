from backend.models.agenda import Agenda, Condition, Effect, Goal, Plan, Step
from backend.models.mps import AgentMethod, MPRegistry
from backend.models.output import OutputXMRTemplate
from backend.models.statement import AddFillerStatement, AssertStatement, AssignFillerStatement, AssignVariableStatement, ExistsStatement, ExpectationStatement, ForEachStatement, IsStatement, MakeInstanceStatement, MeaningProcedureStatement, OutputXMRStatement, TransientFrameStatement
from backend.models.xmr import XMR
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Query import ExistsComparator, IdComparator, Query
from ontograph.Space import Space
from utils.AgentOntoLang import AgentOntoLang, OntoAgentProcessorAddTrigger, OntoAgentProcessorDefineOutputXMRTemplate, OntoAgentProcessorRegisterMP
import unittest


class AgentOntoLangTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        self.ontolang = AgentOntoLang()

    def test_add_trigger(self):
        query = Query().search(ExistsComparator(slot="THEME", filler=123, isa=False))

        processor = OntoAgentProcessorAddTrigger("@SELF.AGENDA.1", "@EXE.MYGOAL.1", query)
        parsed = self.ontolang.parse("ADD TRIGGER TO @SELF.AGENDA.1 INSTANTIATE @EXE.MYGOAL.1 WHEN THEME = 123;")

        self.assertEqual([processor], parsed)

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
        q1 = Query().search(ExistsComparator(slot="THEME", filler=123, isa=False))
        q2 = Query().search(ExistsComparator(slot="THEME", filler=456, isa=False))
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

        statement = AssertStatement.instance(space, ExistsStatement.instance(space, Query().search(ExistsComparator(slot="XYZ", isa=False))), [resolution1])
        parsed = self.ontolang.parse("ASSERT EXISTS XYZ = * ELSE IMPASSE WITH @TEST:@TEST.MYGOAL()")
        self.assertEqual(statement, parsed)

        statement = AssertStatement.instance(space, IsStatement.instance(space, f, "SLOT", 123), [resolution1])
        parsed = self.ontolang.parse("ASSERT @SELF.FRAME[SLOT] == 123 ELSE IMPASSE WITH @TEST:@TEST.MYGOAL()")
        self.assertEqual(statement, parsed)

        statement = AssertStatement.instance(space, MeaningProcedureStatement.instance(space, "some_mp", ["$var1"]), [resolution1])
        parsed = self.ontolang.parse("ASSERT SELF.some_mp($var1) ELSE IMPASSE WITH @TEST:@TEST.MYGOAL()")
        self.assertEqual(statement, parsed)

        statement = AssertStatement.instance(space, ExistsStatement.instance(space, Query().search(ExistsComparator(slot="XYZ", isa=False))), [resolution1, resolution2])
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

        from backend.models.bootstrap import BootstrapTriple

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

        statement = AssignVariableStatement.instance(space, "$var1", ExistsStatement.instance(space, Query().search(IdComparator("@EXE.TEST.1"))))
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

        statement = AssignVariableStatement.instance(space, "$var1", TransientFrameStatement.instance(space, [BootstrapTriple("SLOT", 123)]))
        parsed = self.ontolang.parse("$var1 = {SLOT 123;}")
        self.assertEqual(statement, parsed)

    def test_exists_statement(self):
        self.ontolang.get_starting_rule = lambda: "exists_statement"

        statement = ExistsStatement.instance(Space("SELF"), Query().search(ExistsComparator(slot="THEME", filler=123, isa=False)))
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

        statement = ExpectationStatement.instance(space, ExistsStatement.instance(space, Query().search(ExistsComparator(slot="XYZ", isa=False))))
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

        query = Query().search(ExistsComparator(slot="THEME", filler=123, isa=False))

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

        from backend.models.bootstrap import BootstrapTriple

        property1 = BootstrapTriple("SLOTA", 123)
        property2 = BootstrapTriple("SLOTA", 456)
        property3 = BootstrapTriple("SLOTB", "abc")
        property4 = BootstrapTriple("SLOTC", "$var1")
        property5 = BootstrapTriple("SLOTD", Identifier("@TEST.FRAME.1"))

        statement = TransientFrameStatement.instance(Space("EXE"), [property1])
        parsed = self.ontolang.parse("{SLOTA 123;}")
        self.assertEqual(statement, parsed)

        statement = TransientFrameStatement.instance(Space("EXE"), [property1, property2])
        parsed = self.ontolang.parse("{SLOTA 123; SLOTA 456;}")
        self.assertEqual(statement, parsed)

        statement = TransientFrameStatement.instance(Space("EXE"), [property3, property4, property5])
        parsed = self.ontolang.parse("{SLOTB \"abc\"; SLOTC $var1; SLOTD @TEST.FRAME.1;}")
        self.assertEqual(statement, parsed)


class OntoAgentProcessorAddTriggerTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_call(self):
        agenda = Frame("@TEST.AGENDA")
        definition = Frame("@TEST.DEFINITION")
        query = Query().search(IdComparator("@TEST.SOMETHING.123"))

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
        from ontograph.OntoLang import AssignOntoLangProcessor

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


class TestAgentMethod(AgentMethod):
    pass